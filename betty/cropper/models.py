import errno
import io
import os
import shutil

from django.db import models
from django.dispatch import receiver
from django.core.files import File
from django.core.urlresolvers import reverse

from PIL import Image as PILImage
from PIL import JpegImagePlugin

from betty.conf.app import settings
from betty.cropper.flush import get_cache_flusher
from betty.cropper.tasks import search_image_quality

from jsonfield import JSONField


logger = __import__('logging').getLogger(__name__)


ANIMATED_EXTENSIONS = ['gif', 'jpg']
CROP_EXTENSIONS = ["png", "jpg"]


def source_upload_to(instance, filename):
    return os.path.join(instance.path(), filename)


def optimized_upload_to(instance, filename):
    _path, ext = os.path.splitext(filename)
    return os.path.join(instance.path(), "optimized{}".format(ext))


def optimize_image(image_model, image_buffer, filename):

    im = PILImage.open(image_buffer)

    # Let's cache some important stuff
    format = im.format
    icc_profile = im.info.get("icc_profile")
    quantization = getattr(im, "quantization", None)
    subsampling = None
    if format == "JPEG":
        try:
            subsampling = JpegImagePlugin.get_sampling(im)
        except IndexError:
            # Ignore if sampling fails
            logger.debug('JPEG sampling failed, ignoring')
        except:
            # mparent(2016-03-25): Eventually eliminate "catch all", but need to log errors to see
            # if we're missing any other exception types in the wild
            logger.exception('JPEG sampling error')

    if im.size[0] > settings.BETTY_MAX_WIDTH:
        # If the image is really large, we'll save a more reasonable version as the "original"
        height = settings.BETTY_MAX_WIDTH * float(im.size[1]) / float(im.size[0])
        im = im.resize((settings.BETTY_MAX_WIDTH, int(round(height))), PILImage.ANTIALIAS)

        out_buffer = io.BytesIO()
        if format == "JPEG" and im.mode == "RGB":
            # For JPEG files, we need to make sure that we keep the quantization profile
            try:
                im.save(
                    out_buffer,
                    icc_profile=icc_profile,
                    qtables=quantization,
                    subsampling=subsampling,
                    format="JPEG")
            except ValueError as e:
                # Maybe the image already had an invalid quant table?
                if e.args[:1] == ('Invalid quantization table',):
                    out_buffer = io.BytesIO()  # Make sure it's empty after failed save attempt
                    im.save(
                        out_buffer,
                        icc_profile=icc_profile,
                        format=format,
                    )
                else:
                    raise
        else:
            im.save(out_buffer,
                    icc_profile=icc_profile,
                    format=format)

        image_model.optimized.save(filename, File(out_buffer))

    else:
        # No modifications, just save original as optimized
        image_buffer.seek(0)
        image_model.optimized.save(filename, File(image_buffer))

    image_model.save()


class Ratio(object):

    def __init__(self, ratio):
        self.string = ratio
        self.height = 0
        self.width = 0

        if ratio != "original":
            if len(ratio.split("x")) != 2:
                raise ValueError("Improper ratio!")
            self.width = int(ratio.split("x")[0])
            self.height = int(ratio.split("x")[1])


class ImageManager(models.Manager):

    def create_from_path(self, path, filename=None, name=None, credit=None):
        """Creates an image object from a TemporaryUploadedFile insance"""

        image_buffer = io.BytesIO(open(path, 'rb').read())

        im = PILImage.open(image_buffer)
        if filename is None:
            filename = os.path.split(path)[1]
        if name is None:
            name = filename

        image = self.create(
            name=name,
            credit=credit,
            width=im.size[0],
            height=im.size[1]
        )

        # Copy temp image file to S3
        image_buffer.seek(0)
        image.source.save(filename, File(image_buffer))

        # If the image is a GIF, we need to do some special stuff
        if im.format == "GIF":
            image.animated = True

        image.save()

        # Use temp image path (instead of pulling from S3)
        image_buffer.seek(0)
        optimize_image(image_model=image, image_buffer=image_buffer, filename=filename)

        if settings.BETTY_JPEG_QUALITY_RANGE:
            search_image_quality.apply_async(args=(image.id,))

        return image


def save_crop_to_disk(image_data, path):

    try:
        os.makedirs(os.path.dirname(path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

    with open(path, 'wb+') as out:
        out.write(image_data)


def _read_from_storage(file_field):
    """Convenience wrapper to ensure entire file is read and properly closed."""
    if file_field:
        file_field.open()
        tmp = io.BytesIO(file_field.read())
        file_field.close()
        return tmp


class Image(models.Model):

    name = models.CharField(max_length=255)
    credit = models.CharField(max_length=120, null=True, blank=True)

    source = models.FileField(upload_to=source_upload_to,
                              max_length=255, null=True, blank=True)
    optimized = models.FileField(upload_to=optimized_upload_to,
                                 max_length=255, null=True, blank=True)

    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)

    selections = JSONField(null=True, blank=True)

    jpeg_quality = models.IntegerField(null=True, blank=True)
    jpeg_quality_settings = JSONField(null=True, blank=True)
    animated = models.BooleanField(default=False)

    # Used for "If-Modified-Since/304" handling
    last_modified = models.DateTimeField(auto_now=True)

    objects = ImageManager()

    class Meta:
        permissions = (
            ("read", "Can search images, and see the detail data"),
            ("crop", "Can crop images")
        )

    @property
    def id_string(self):
        id_string = ""
        for index, char in enumerate(str(self.id)):
            if index % 4 == 0 and index != 0:
                id_string += "/"
            id_string += char
        return id_string

    @property
    def best(self):
        """Convenience method to prefer optimzied over source image, if available."""
        if self.optimized:
            return self.optimized
        else:
            return self.source

    def read_best_bytes(self):
        return _read_from_storage(self.best)

    def read_source_bytes(self):
        return _read_from_storage(self.source)

    def read_optimized_bytes(self):
        return _read_from_storage(self.optimized)

    def get_height(self):
        """Lazily returns the height of the image

        If the width exists in the database, that value will be returned,
        otherwise the width will be read source image."""
        if not self.height:
            self._refresh_dimensions()
        return self.height

    def get_width(self):
        """Lazily returns the width of the image

        If the width exists in the database, that value will be returned,
        otherwise the width will be read source image."""
        if not self.width:
            self._refresh_dimensions()
        return self.width

    def _refresh_dimensions(self):
        img = PILImage.open(self.read_source_bytes())
        self.height = img.size[1]
        self.width = img.size[0]

    def get_selection(self, ratio):
        """Returns the image selection for a given ratio

        If the selection for this ratio has been set manually, that value
        is returned exactly, otherwise the selection is auto-generated."""

        # This is kiiiiinda a hack. If we have an optimized image, hack up the height and width.
        if self.width > settings.BETTY_MAX_WIDTH and self.optimized:
            height = settings.BETTY_MAX_WIDTH * float(self.height) / float(self.width)
            self.height = int(round(height))
            self.width = settings.BETTY_MAX_WIDTH

        selection = None
        if self.selections is not None:
            if ratio.string in self.selections:
                selection = self.selections.get(ratio.string)

                # Here I need to check for all kinds of bad data.
                if selection['y1'] > self.get_height() or selection['x1'] > self.get_width():
                    selection = None
                elif selection['y1'] < selection['y0'] or selection['x1'] < selection['x0']:
                    selection = None
                else:
                    for key in ('x0', 'x1', 'y0', 'y1'):
                        if selection[key] < 0:
                            selection = None
                            break

        if selection is None:
            source_aspect = self.get_width() / float(self.get_height())
            selection_aspect = ratio.width / float(ratio.height)

            min_x = 0
            min_y = 0

            max_x = self.get_width()
            max_y = self.get_height()

            if source_aspect > selection_aspect:
                offset = (max_x - (max_y * ratio.width / ratio.height)) / 2.0
                min_x = offset
                max_x -= offset
            if source_aspect < selection_aspect:
                offset = (max_y - (max_x * ratio.height / ratio.width)) / 2.0
                min_y = offset
                max_y -= offset
            selection = {
                'x0': int(min_x),
                'y0': int(min_y),
                'x1': int(max_x),
                'y1': int(max_y)
            }

        if selection['y1'] > self.get_height():
            selection['y1'] = int(self.get_height())

        if selection['x1'] > self.get_width():
            selection['x1'] = int(self.get_width())

        if selection['x0'] < 0:
            selection['x0'] = 0

        if selection['y0'] < 0:
            selection['y0'] = 0

        return selection

    def clear_crops(self, ratios=None):
        if ratios is None:
            ratios = list(settings.BETTY_RATIOS)
            ratios.append("original")

        # Optional cache flush support
        flusher = get_cache_flusher()
        if flusher:
            paths = []
            for ratio_slug in ratios:
                # Since might now know which formats to flush (since maybe not saving crops to
                # disk), need to flush all possible crops.
                paths += [self.get_absolute_url(ratio=ratio_slug, width=width, extension=extension)
                          for extension in CROP_EXTENSIONS
                          for width in sorted(set(settings.BETTY_WIDTHS +
                                                  settings.BETTY_CLIENT_ONLY_WIDTHS))]
            if self.animated:
                for extension in ANIMATED_EXTENSIONS:
                    paths.append(self.get_animated_url(extension=extension))

            flusher(paths)

        # Optional disk crops support
        if settings.BETTY_SAVE_CROPS_TO_DISK:
            for ratio_slug in (ratios + ['animated']):
                ratio_path = os.path.join(self.path(), ratio_slug)
                if os.path.exists(ratio_path):
                    shutil.rmtree(ratio_path)

    def get_jpeg_quality(self, width):
        quality = None

        if self.jpeg_quality_settings:
            closest = 0
            for w, q in self.jpeg_quality_settings.items():
                if abs(width - int(w)) < abs(width - closest):
                    closest = int(w)

            quality = self.jpeg_quality_settings[w]

        return quality

    def path(self, root=None):
        id_string = ""
        for index, char in enumerate(str(self.id)):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        if root is None:
            root = settings.BETTY_IMAGE_ROOT
        return os.path.join(root, id_string[1:])

    def get_animated(self, extension):
        """Legacy (Pre-v2.0) animated behavior.
        Originally betty just wrote these to disk on image creation and let NGINX try-files
        automatically serve these animated GIF + JPG.
        """

        assert self.animated

        img_bytes = self.read_best_bytes()
        if extension == "jpg":
            # Thumbnail
            img = PILImage.open(img_bytes)
            if img.mode != "RGB":
                img = img.convert("RGB")
            img_bytes = io.BytesIO()
            img.save(img_bytes, "JPEG")
        elif extension != "gif":
            raise Exception('Unsupported extension')

        if settings.BETTY_SAVE_CROPS_TO_DISK:
            save_crop_to_disk(img_bytes.getvalue(),
                              os.path.join(self.path(settings.BETTY_SAVE_CROPS_TO_DISK_ROOT),
                                           'animated',
                                           'original.{}'.format(extension)))

        return img_bytes.getvalue()

    def crop(self, ratio, width, extension):
        img = PILImage.open(self.read_best_bytes())

        icc_profile = img.info.get("icc_profile")

        if ratio.string == 'original':
            ratio.width = img.size[0]
            ratio.height = img.size[1]

        selection = self.get_selection(ratio)
        try:
            img = img.crop((selection['x0'], selection['y0'], selection['x1'], selection['y1']))
        except ValueError:
            # Looks like we have bad height and width data. Let's reload that and try again.
            self.width = img.size[0]
            self.height = img.size[1]
            self.save()

            selection = self.get_selection(ratio)
            img = img.crop((selection['x0'], selection['y0'], selection['x1'], selection['y1']))

        height = int(round(width * float(ratio.height) / float(ratio.width)))
        img = img.resize((width, height), PILImage.ANTIALIAS)

        if extension == "jpg":
            if img.mode != "RGB":
                img = img.convert("RGB")
            pillow_kwargs = {"format": "jpeg"}

            if self.get_jpeg_quality(width):
                pillow_kwargs["quality"] = self.get_jpeg_quality(width)
            elif img.format == "JPEG":
                pillow_kwargs["quality"] = "keep"
            else:
                pillow_kwargs["quality"] = settings.BETTY_DEFAULT_JPEG_QUALITY

        if extension == "png":
            pillow_kwargs = {"format": "png"}

        if icc_profile:
            pillow_kwargs["icc_profile"] = icc_profile

        tmp = io.BytesIO()
        img.save(tmp, **pillow_kwargs)

        if settings.BETTY_SAVE_CROPS_TO_DISK:
            # We only want to save this to the filesystem if it's one of our usual widths.
            if width in settings.BETTY_WIDTHS or not settings.BETTY_WIDTHS:
                ratio_dir = os.path.join(self.path(settings.BETTY_SAVE_CROPS_TO_DISK_ROOT),
                                         ratio.string)
                save_crop_to_disk(tmp.getvalue(),
                                  os.path.join(ratio_dir, "%d.%s" % (width, extension)))

        return tmp.getvalue()

    def get_absolute_url(self, ratio="original", width=600, extension="jpg"):
        return reverse("betty.cropper.views.crop", kwargs={
            "id": self.id_string,
            "ratio_slug": ratio,
            "width": width,
            "extension": extension
        })

    def get_animated_url(self, extension="gif"):
        return reverse("betty.cropper.views.animated", kwargs={
            "id": self.id_string,
            "extension": extension
        })

    def to_native(self):
        """Returns a Python dictionary, sutiable for Serialization"""

        # This is kiiiiinda a hack. If we have an optimized image, hack up the height and width.
        if self.width > settings.BETTY_MAX_WIDTH and self.optimized:
            height = settings.BETTY_MAX_WIDTH * float(self.height) / float(self.width)
            self.height = int(round(height))
            self.width = settings.BETTY_MAX_WIDTH

        data = {
            'id': self.id,
            'name': self.name,
            'width': self.get_width(),
            'height': self.get_height(),
            'credit': self.credit,
            'selections': {}
        }
        for ratio in settings.BETTY_RATIOS:
            data['selections'][ratio] = self.get_selection(Ratio(ratio))
            data['selections'][ratio]["source"] = "auto"
            if self.selections and data['selections'][ratio] == self.selections.get(ratio):
                data['selections'][ratio]["source"] = "user"
        return data

    def cache_key(self):
        """
        Returns string unique to cache instance
        """
        return "image-{}".format(self.id)


@receiver(models.signals.post_delete, sender=Image)
def auto_flush_and_delete_files_on_delete(sender, instance, **kwargs):
    instance.clear_crops()
    for file_field in [instance.source, instance.optimized]:
        if file_field:
            file_field.delete(save=False)
