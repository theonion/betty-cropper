import base64
import hashlib
import random

from django.db import models
from django.db.models.manager import EmptyManager
from django.contrib.auth.models import Group


class BettyCropperUser(object):
    id = None
    pk = None
    username = ''
    is_staff = False
    is_active = False
    is_superuser = False
    _groups = EmptyManager(Group)

    def __init__(self, permissions):
        self._permissions = permissions

    def __str__(self):
        return 'AnonymousUser'

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return 1  # instances always return the same hash value

    def save(self):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def delete(self):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def set_password(self, raw_password):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def check_password(self, raw_password):
        raise NotImplementedError("Django doesn't provide a DB representation for AnonymousUser.")

    def _get_groups(self):
        return self._groups
    groups = property(_get_groups)

    def _get_user_permissions(self):
        return self._permissions
    user_permissions = property(_get_user_permissions)

    def get_group_permissions(self, obj=None):
        return set()

    def get_all_permissions(self, obj=None):
        return self._permissions

    def has_perm(self, perm, obj=None):
        return perm in self._permissions

    def has_perms(self, perm_list, obj=None):
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, module):
        return module == "server" and self._permissions

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True


class ApiTokenManager(models.Manager):
    def random_token(self):
        random_256 = hashlib.sha256(str(random.getrandbits(256))).digest()
        random_encode = random.choice(['rA', 'aZ', 'gQ', 'hH', 'hG', 'aR', 'DD'])
        return base64.b64encode(random_256, random_encode).rstrip('==')

    def create_superuser(self):
        return self.create(
            image_read_permission=True,
            image_change_permission=True,
            image_crop_permission=True,
            image_add_permsission=True,
            image_delete_permission=True
        )

    def create_cropping_user(self):
        return self.create(
            image_read_permission=True,
            image_crop_permission=True
        )

    def create_standard_user(self):
        return self.create(
            image_read_permission=True,
            image_change_permission=True,
            image_crop_permission=True,
            image_add_permsission=True,
        )


class ApiToken(models.Model):

    objects = ApiTokenManager()

    public_token = models.CharField(max_length=255, unique=True, default=objects.random_token)
    private_token = models.CharField(max_length=255, default=objects.random_token)

    image_read_permission = models.BooleanField(default=False)
    image_change_permission = models.BooleanField(default=False)
    image_crop_permission = models.BooleanField(default=False)
    image_add_permsission = models.BooleanField(default=False)
    image_delete_permission = models.BooleanField(default=False)

    def get_user(self):
        permissions = []
        if self.image_read_permission:
            permissions.append("server.image_read")
        if self.image_change_permission:
            permissions.append("server.image_change")
        if self.image_crop_permission:
            permissions.append("server.image_crop")
        if self.image_add_permsission:
            permissions.append("server.image_add")
        if self.image_delete_permission:
            permissions.append("server.image_delete")
        return BettyCropperUser(permissions)
