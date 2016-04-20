# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
try:
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urljoin

from django.conf import settings as _settings

from django.apps import AppConfig


class BettyConfConfig(AppConfig):
    name = 'rock_n_roll'
    verbose_name = "Rock ’n’ roll"


PACKAGE_DIR = os.path.dirname(os.path.dirname(__file__))

DEFAULTS = {
    "BETTY_IMAGE_ROOT": os.path.join(_settings.MEDIA_ROOT, "images"),
    "BETTY_IMAGE_URL": urljoin(_settings.MEDIA_URL, "images/"),
    "BETTY_IMAGE_URL_USE_REQUEST_HOST": False,
    "BETTY_RATIOS": ("1x1", "2x1", "3x1", "3x4", "4x3", "16x9"),
    "BETTY_WIDTHS": [],
    "BETTY_CLIENT_ONLY_WIDTHS": [],
    "BETTY_PLACEHOLDER": _settings.DEBUG,
    "BETTY_PLACEHOLDER_COLORS": (
        (153, 153, 51),
        (102, 153, 51),
        (51, 153, 51),
        (153, 51, 51),
        (194, 133, 71),
        (51, 153, 102),
        (153, 51, 102),
        (71, 133, 194),
        (51, 153, 153),
        (153, 51, 153)
    ),
    "BETTY_PLACEHOLDER_FONT": os.path.join(PACKAGE_DIR, "cropper/font/OpenSans-Semibold.ttf"),
    "BETTY_PUBLIC_TOKEN": None,
    "BETTY_PRIVATE_TOKEN": None,
    "BETTY_CACHE_FLUSHER": None,
    "BETTY_DEFAULT_IMAGE": None,
    "BETTY_MAX_WIDTH": 3200,
    "BETTY_DEFAULT_JPEG_QUALITY": 80,
    "BETTY_JPEG_MAX_ERROR": 3.5,
    "BETTY_JPEG_QUALITY_RANGE": None,
    "BETTY_SAVE_CROPS_TO_DISK": True,  # On by default (per legacy behavior)
    "BETTY_SAVE_CROPS_TO_DISK_ROOT": None,   # If not set, will use BETTY_IMAGE_ROOT
    "BETTY_CACHE_CROP_SEC": 300,
    "BETTY_CACHE_CROP_NON_BREAKPOINT_SEC": None,  # If not set, will use BETTY_CACHE_CROP_SEC
    "BETTY_CACHE_IMAGEJS_SEC": 300,
}


class BettySettings(object):
    '''
    Lazy Django settings wrapper for Betty Cropper
    '''
    def __init__(self, wrapped_settings):
        self.wrapped_settings = wrapped_settings

    def __getattr__(self, name):
        if hasattr(self.wrapped_settings, name):
            return getattr(self.wrapped_settings, name)
        elif name in DEFAULTS:
            return DEFAULTS[name]
        else:
            raise AttributeError("'{0}' setting not found".format(name))

settings = BettySettings(_settings)
