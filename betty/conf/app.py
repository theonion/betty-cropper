# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import urlparse

from django.conf import settings as _settings

DEFAULTS = {
    "BETTY_IMAGE_ROOT": os.path.join(_settings.MEDIA_ROOT, "images"),
    "BETTY_IMAGE_URL": urlparse.urljoin(_settings.MEDIA_URL, "images/"),
    "BETTY_RATIOS": ("1x1", "2x1", "3x1", "3x4", "4x3", "16x9"),
    "BETTY_WIDTHS": (80, 150, 240, 300, 320, 400, 480, 620, 640, 820, 960, 1200, 1600),
    "BETTY_PLACEHOLDER": _settings.DEBUG,
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
