import io
import os
import shutil

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse

from PIL import Image as PILImage
from PIL import JpegImagePlugin

from betty.conf.app import settings
from betty.cropper.tasks import search_image_quality

from jsonfield import JSONField


betty_storage = FileSystemStorage(
    location=settings.BETTY_IMAGE_ROOT,
    base_url=settings.BETTY_IMAGE_URL
)


def source_upload_to(instance, filename):
    return os.path.join(instance.path(), filename)


def optimized_upload_to(instance, filename):
    path, ext = os.path.splitext(filename)
    return os.path.join(instance.path(), "optimized{}".format(ext))


def optimize_image(image):

    im = PILImage.open(image.source.path)
    
    # Let's cache some important stuff
    format = im.format
    icc_profile = im.info.get("icc_profile")
    quantization = getattr(im, "quantization", None)
    subsampling = None
    if format == "JPEG":
        try:
            subsampling = JpegImagePlugin.get_sampling(im)
        except:
            pass  # Sometimes, crazy images exist.

    filename = os.path.split(image.source.path)[1]

    if im.size[0] > settings.BETTY_MAX_WIDTH:
        # If the image is really large, we'll save a more reasonable version as the "original"
        height = settings.BETTY_MAX_WIDTH * float(im.size[1]) / float(im.size[0])
        im = im.resize((settings.BETTY_MAX_WIDTH, int(round(height))), PILImage.ANTIALIAS)

    image.optimized.name = optimized_upload_to(image, filename)
    if format == "JPEG" and im.mode == "RGB":
        # For JPEG files, we need to make sure that we keep the quantization profile
        try:
            im.save(
                image.optimized.name,
                icc_profile=icc_profile,
                qtables=quantization,
                subsampling=subsampling,
                format="JPEG")
        except (TypeError, ValueError) as e:
            # Maybe the image already had an invalid quant table?
            if e.message.startswith("Not a valid numbers of quantization tables"):
                im.save(
                    image.optimized.name,
                    icc_profile=icc_profile
                )
            else:
                raise
    else:
        im.save(image.optimized.name, icc_profile=icc_profile)
    image.save()


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

        im = PILImage.open(path)
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

        os.makedirs(image.path())

        # Let's make sure we copy the temp file to the source location
        source_path = source_upload_to(image, filename)
        shutil.copy(path, source_path)
        image.source.name = source_path

        # If the image is a GIF, we need to do some special stuff
        if im.format == "GIF":
            image.animated = True

            os.makedirs(os.path.join(image.path(), "animated"))

            # First, let's copy the original
            animated_path = os.path.join(image.path(), "animated/original.gif")
            shutil.copy(path, animated_path)
            os.chmod(animated_path, 744)
            
            # Next, we'll make a thumbnail of the original
            still_path = os.path.join(image.path(), "animated/original.jpg")
            if im.mode != "RGB":
                jpeg = im.convert("RGB")
                jpeg.save(still_path, "JPEG")
            else:
                im.save(still_path, "JPEG")
    
        image.save()
        optimize_image(image)

        if settings.BETTY_JPEG_QUALITY_RANGE:
            search_image_quality.apply_async(args=(image.id,))

        return image


class Image(models.Model):

    name = models.CharField(max_length=255)
    credit = models.CharField(max_length=120, null=True, blank=True)

    source = models.FileField(upload_to=source_upload_to, storage=betty_storage, max_length=255, null=True, blank=True)
    optimized = models.FileField(upload_to=optimized_upload_to, storage=betty_storage, max_length=255, null=True, blank=True)
    
    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)

    selections = JSONField(null=True, blank=True)

    jpeg_quality = models.IntegerField(null=True, blank=True)
    animated = models.BooleanField(default=False)

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

    def get_height(self):
        """Lazily returns the height of the image

        If the width exists in the database, that value will be returned,
        otherwise the width will be read from the filesystem."""
        if self.height in (None, 0):
            img = PILImage.open(self.source.path)
            self.height = img.size[1]
            self.width = img.size[0]
        return self.height

    def get_width(self):
        """Lazily returns the width of the image

        If the width exists in the database, that value will be returned,
        otherwise the width will be read from the filesystem."""
        if self.width in (None, 0):
            img = PILImage.open(self.source.path)
            self.height = img.size[1]
            self.width = img.size[0]
        return self.width

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

    def path(self):
        id_string = ""
        for index, char in enumerate(str(self.id)):
            if index % 4 == 0:
                id_string += "/"
            id_string += char
        return os.path.join(settings.BETTY_IMAGE_ROOT, id_string[1:])

    def crop(self, ratio, width, extension, fp=None):
        if self.optimized:
            img = PILImage.open(self.optimized.path)
        else:
            img = PILImage.open(self.source.path)
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
            if self.jpeg_quality:
                pillow_kwargs["quality"] = self.jpeg_quality
            elif img.format == "JPEG":
                pillow_kwargs["quality"] = "keep"
            else:
                pillow_kwargs["quality"] = settings.BETTY_DEFAULT_JPEG_QUALITY

        if extension == "png":
            pillow_kwargs = {"format": "png"}

        if icc_profile:
            pillow_kwargs["icc_profile"] = icc_profile

        if width in settings.BETTY_WIDTHS or len(settings.BETTY_WIDTHS) == 0:
            ratio_dir = os.path.join(self.path(), ratio.string)
            # We only want to save this to the filesystem if it's one of our usual widths.
            try:
                os.makedirs(ratio_dir)
            except OSError as e:
                if e.errno != 17:
                    raise e

            with open(os.path.join(ratio_dir, "%d.%s" % (width, extension)), 'wb+') as out:
                img.save(out, **pillow_kwargs)

        tmp = io.BytesIO()
        img.save(tmp, **pillow_kwargs)

        return tmp.getvalue()

    def get_absolute_url(self, ratio="original", width=600, format="jpg"):
        return reverse("betty.cropper.views.crop", kwargs={
            "id": self.id_string,
            "ratio_slug": ratio,
            "width": width,
            "extension": format
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
