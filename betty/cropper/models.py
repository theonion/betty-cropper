import io
import os

from django.db import models
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse

from PIL import Image as PILImage

from betty.conf.app import settings

from jsonfield import JSONField


betty_storage = FileSystemStorage(
    location=settings.BETTY_IMAGE_ROOT,
    base_url=settings.BETTY_IMAGE_URL
)


def source_upload_to(instance, filename):
    return os.path.join(instance.path(), filename)


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


class Image(models.Model):

    source = models.FileField(upload_to=source_upload_to, storage=betty_storage, max_length=255)
    name = models.CharField(max_length=255)
    height = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    credit = models.CharField(max_length=120, null=True, blank=True)
    selections = JSONField(null=True, blank=True)

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
            img = PILImage.open(self.src_path())
            self.height = img.size[1]
            self.width = img.size[0]
        return self.height

    def get_width(self):
        """Lazily returns the width of the image

        If the width exists in the database, that value will be returned,
        otherwise the width will be read from the filesystem."""
        if self.width in (None, 0):
            img = PILImage.open(self.src_path())
            self.height = img.size[1]
            self.width = img.size[0]
        return self.width

    def get_selection(self, ratio):
        """Returns the image selection for a given ratio

        If the selection for this ratio has been set manually, that value
        is returned exactly, otherwise the selection is auto-generated."""
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
        img = PILImage.open(self.src_path())
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

        if extension == 'jpg':
            pillow_kwargs = {"format": "jpeg", "quality": 80}
        if extension == 'png':
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
        return data

    def src_path(self):
        return self.source.path
