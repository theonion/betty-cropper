import requests

from django import forms

try:  # Django < 1.5 doesn't have checks, so we'll just ignore that.
    from django.core import checks
except ImportError:
    pass

from django.core.cache import cache
from django.db.models.fields import Field
from django.core.files.base import File
from django.db.models.fields.files import FieldFile, FileDescriptor
from django.utils.translation import ugettext_lazy as _


from betty.storage import BettyCropperStorage

default_storage = BettyCropperStorage()


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^betty\.cropped\.fields\.ImageField"])


class ImageFieldFile(FieldFile):
    
    def __init__(self, instance, field, id):
        super(ImageFieldFile, self).__init__(instance, field, None)
        self.id = id
        self._name = None

    def __bool__(self):
        return bool(self.id)

    def __nonzero__(self):
        return bool(self.id)

    @property
    def name(self):
        if not self.id:
            return None

        cache_key = "betty-cropper-names-{0}".format(self.id)
        self._name = self._name or cache.get(cache_key)
        if not self._name:

            detail_url = "{base_url}/api/{id}".format(base_url=self.field.storage.base_url, id=self.id)
            response = requests.get(detail_url, headers=self.field.storage.auth_headers)
            self._name = response.json()["name"]
            cache.set(cache_key, self._name)

        return self._name

    @name.setter
    def name(self, value):
        pass

    @property
    def alt(self):
        if self.field.alt_field:
            return getattr(self.instance, self.field.alt_field)
        return None

    @alt.setter
    def alt(self, value):
        setattr(self.instance, self.field.alt_field, value)

    @property
    def caption(self):
        if self.field.caption_field:
            return getattr(self.instance, self.field.caption_field)
        return None

    @caption.setter
    def caption(self, value):
        setattr(self.instance, self.field.caption_field, value)

    def __eq__(self, other):
        # Older code may be expecting FileField values to be simple strings.
        # By overriding the == operator, it can remain backwards compatibility.
        if hasattr(other, 'id'):
            return self.id == other.id
        return self.id == other

    def __hash__(self):
        return hash(self.id)

    def save(self, name, content, save=True):
        self.id = self.storage.save(name, content)
        self._name = name
        setattr(self.instance, self.field.name, self)

        # Update the filesize cache
        self._committed = True

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()
    save.alters_data = True

    def delete(self, save=True):
        raise NotImplemented("You can't delete a remote image this way")

    def get_crop_url(self, ratio="original", width=600, format="jpg"):
        return self.storage.url(self.id, ratio=ratio, width=width, format=format)


class ImageDescriptor(FileDescriptor):
    """A custom descriptor for a Betty Cropper image

    This is almost an exact replica of the FileDescriptor class, with
    the notable exception that it works using an integer as an initial
    value, rather than a string."""

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))

        file = instance.__dict__[self.field.name]
        if isinstance(file, int) or file is None:
            attr = self.field.attr_class(instance, self.field, file)
            instance.__dict__[self.field.name] = attr

        elif isinstance(file, File) and not isinstance(file, ImageFieldFile):
            file_copy = self.field.attr_class(instance, self.field, file.name)
            file_copy.file = file
            file_copy._committed = False
            instance.__dict__[self.field.name] = file_copy

        elif isinstance(file, FieldFile) and not hasattr(file, 'field'):
            file.instance = instance
            file.field = self.field
            file.storage = self.field.storage

        # That was fun, wasn't it?
        return instance.__dict__[self.field.name]


class ImageField(Field):
    """Mostly just a clone of FileField, but with some betty-specific functionality

    Unfortunately, this can't be a subcalss of FileField, or else Django will
    freak out that this is a FileField and doesn't have an upload_to value"""

    attr_class = ImageFieldFile
    descriptor_class = ImageDescriptor
    description = _("ImageField")

    def __init__(self, verbose_name=None, name=None, storage=None, caption_field=None, alt_field=None, **kwargs):
        self._primary_key_set_explicitly = 'primary_key' in kwargs
        self._unique_set_explicitly = 'unique' in kwargs
        self.caption_field, self.alt_field = caption_field, alt_field

        self.storage = storage or default_storage
        if "default" not in kwargs:
            kwargs["default"] = None
        super(ImageField, self).__init__(verbose_name, name, **kwargs)

    def check(self, **kwargs):
        errors = super(ImageField, self).check(**kwargs)
        errors.extend(self._check_unique())
        errors.extend(self._check_primary_key())
        return errors

    def _check_unique(self):
        if self._unique_set_explicitly:
            return [
                checks.Error(
                    "'unique' is not a valid argument for a %s." % self.__class__.__name__,
                    hint=None,
                    obj=self,
                    id='fields.E200',
                )
            ]
        else:
            return []

    def _check_primary_key(self):
        if self._primary_key_set_explicitly:
            return [
                checks.Error(
                    "'primary_key' is not a valid argument for a %s." % self.__class__.__name__,
                    hint=None,
                    obj=self,
                    id='fields.E201',
                )
            ]
        else:
            return []

    def deconstruct(self):
        name, path, args, kwargs = super(ImageField, self).deconstruct()
        if self.storage is not default_storage:
            kwargs['storage'] = self.storage
        if self.caption_field:
            kwargs["caption_field"] = self.caption_field
        if self.alt_field:
            kwargs["alt_field"] = self.alt_field
        return name, path, args, kwargs

    def get_internal_type(self):
        return "IntegerField"

    def get_prep_value(self, value):
        if value is None:
            return None
        return value

    def get_prep_lookup(self, lookup_type, value):
        return super(ImageField, self).get_prep_lookup(lookup_type, value.id)

    def pre_save(self, model_instance, add):
        "Returns field's value just before saving."
        image_file = super(ImageField, self).pre_save(model_instance, add)
        if image_file and not image_file._committed:
            print(image_file.id)
            # Commit the file to storage prior to saving the model
            image_file.save(image_file.name, image_file, save=False)
        return image_file.id

    def contribute_to_class(self, cls, name):
        super(ImageField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self.descriptor_class(self))

    def save_form_data(self, instance, data):
        # Important: None means "no change", other false value means "clear"
        # This subtle distinction (rather than a more explicit marker) is
        # needed because we need to consume values that are also sane for a
        # regular (non Model-) Form to find in its cleaned_data dictionary.
        if data is not None:
            # This value will be converted to unicode and stored in the
            # database, so leaving False as-is is not acceptable.
            if not data:
                data = ''
            setattr(instance, self.name, data)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FileField, 'max_length': self.max_length}
        # If a file has been provided previously, then the form doesn't require
        # that a new file is provided this time.
        # The code to mark the form field as not required is used by
        # form_for_instance, but can probably be removed once form_for_instance
        # is gone. ModelForm uses a different method to check for an existing file.
        if 'initial' in kwargs:
            defaults['required'] = False
        defaults.update(kwargs)
        return super(ImageField, self).formfield(**defaults)


