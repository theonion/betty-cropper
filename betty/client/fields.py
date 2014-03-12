from django.db.models.fields.files import FieldFile, FileField


class ImageFieldFile(FieldFile):
    pass


class ImageField(FileField):
    pass
