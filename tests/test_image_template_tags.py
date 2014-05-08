from django.template import Template, Context
from django.test import TestCase


from tests.testapp.models import TestModel


class TemplateTagTestCase(TestCase):

    def test_cropped_template_tag(self):
        test_object = TestModel()
        test_object.listing_image.id = 12345
        t = Template("{% load betty %}{% cropped image %}")
        c = Context({"image": test_object.listing_image})
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/original/600.jpg" />')

        t = Template('{% load betty %}{% cropped image width=900 ratio="16x9" format="png" %}')
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/16x9/900.png" />')

    def test_cropped_url_template_tag(self):
        test_object = TestModel()
        test_object.listing_image.id = 12345
        t = Template('{% load betty %}<img src="{% cropped_url image %}" />')
        c = Context({"image": test_object.listing_image})
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/original/600.jpg" />')

        t = Template('{% load betty %}<img src="{% cropped_url image width=900 ratio="16x9" format="png" %}" />')
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/16x9/900.png" />')

    def test_image_id(self):
        t = Template('{% load betty %}<img src="{% cropped_url image %}" />')
        c = Context({"image": 12345})
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/original/600.jpg" />')

        c = Context({"image": "12345"})
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/original/600.jpg" />')

        c = Context({"image": ""})
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/666/original/600.jpg" />')

        c = Context({"image": None})
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/666/original/600.jpg" />')
