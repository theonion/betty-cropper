import base64
import hashlib
import random

from django.db import models
from django.contrib.auth.models import AbstractUser


def random_api_key():
    random_256 = hashlib.sha256(str(random.getrandbits(256))).digest()
    random_encode = random.choice(['rA', 'aZ', 'gQ', 'hH', 'hG', 'aR', 'DD'])
    return base64.b64encode(random_256, random_encode).rstrip('==')


class AuthTokenMixin(object):
    api_key = models.CharField(max_length=255, default=random_api_key)


class User(AbstractUser, AuthTokenMixin):
    pass
