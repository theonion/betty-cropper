import math

from django.core import exceptions
from django.db.models.fields.files import FieldFile, FileField
from django.utils.translation import ugettext_lazy as _


from betty.client.storage import BettyCropperStorage


class ImageFieldFile(FieldFile):
    pass


class ImageField(FileField):

    attr_class = ImageFieldFile

    def __init__(self, verbose_name=None, name=None, storage=BettyCropperStorage, **kwargs):

        super(self, ImageField).__init__(
            verbose_name=verbose_name,
            name=name,
            storage=storage,
            **kwargs)

    empty_strings_allowed = False
    default_error_messages = {
        'invalid': _("'%(value)s' value must be an integer."),
    }

    def to_python(self, value):
        if value is None:
            return value
        try:
            return str(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                self.error_messages['invalid'],
                code='invalid',
                params={'value': value},
            )

    def get_prep_value(self, value):
        value = super(ImageField, self).get_prep_value(value)
        if value is None:
            return None
        return int(value)

    def get_prep_lookup(self, lookup_type, value):
        if ((lookup_type == 'gte' or lookup_type == 'lt')
                and isinstance(value, float)):
            value = math.ceil(value)
        return super(ImageField, self).get_prep_lookup(lookup_type, value)

    def get_internal_type(self):
        return "IntegerField"
