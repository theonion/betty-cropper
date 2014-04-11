from django.template import Template, Context
from django.test import TestCase

from betty.cropper.models import Image

from tests.testapp.models import TestModel


class TemplateTagTestCase(TestCase):

    def test_id_string(self):
        test_object = TestModel()
        test_object.listing_image.id = 12345
        t = Template("{% load betty %}{% cropped image %}")
        c = Context({
            "image": test_object.listing_image
        })
        rendered = t.render(c)
        self.assertEquals(rendered, '<img src="/images/1234/5/original/600.jpg" />')

    def test_image_url(self):
        image = Image.objects.create(id=123456)
        self.assertEquals(image.get_absolute_url(), "/images/1234/56/original/600.jpg")

        self.assertEquals(image.get_absolute_url(format="png"), "/images/1234/56/original/600.png")
        self.assertEquals(image.get_absolute_url(width=900), "/images/1234/56/original/900.jpg")
        self.assertEquals(image.get_absolute_url(ratio="16x9"), "/images/1234/56/16x9/600.jpg")
        self.assertEquals(image.get_absolute_url(format="png", width=900, ratio="16x9"), "/images/1234/56/16x9/900.png")

        image = Image.objects.create(id=123)
        self.assertEquals(image.get_absolute_url(), "/images/123/original/600.jpg")

