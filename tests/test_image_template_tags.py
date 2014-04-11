from django.template import Template, Context
from django.test import TestCase


from tests.testapp.models import TestModel


class TemplateTagTestCase(TestCase):

    def test_cropped_template_tag(self):
        test_object = TestModel()
        test_object.listing_image = 12345
        t = Template("{% load betty %}{% cropped image %}")
        c = Context({"image": test_object.listing_image})
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/original/600.jpg" />')

        t = Template('{% load betty %}{% cropped image width=900 ratio="16x9" format="png" %}')
        self.assertEquals(t.render(c), '<img src="http://localhost:8081/images/1234/5/16x9/900.png" />')
