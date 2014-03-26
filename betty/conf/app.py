# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from six.moves.urllib.parse import urljoin

from django.conf import settings as _settings

DEFAULTS = {
    "BETTY_IMAGE_ROOT": os.path.join(_settings.MEDIA_ROOT, "images"),
    "BETTY_IMAGE_URL": urljoin(_settings.MEDIA_URL, "images/"),
    "BETTY_RATIOS": ("1x1", "2x1", "3x1", "3x4", "4x3", "16x9"),
    "BETTY_WIDTHS": [],
    "BETTY_PLACEHOLDER": _settings.DEBUG,
    "BETTY_PLACEHOLDER_COLORS": (
        "rgb(153,153,51)",
        "rgb(102,153,51)",
        "rgb(51,153,51)",
        "rgb(153,51,51)",
        "rgb(194,133,71)",
        "rgb(51,153,102)",
        "rgb(153,51,102)",
        "rgb(71,133,194)",
        "rgb(51,153,153)",
        "rgb(153,51,153)",
    ),
    "BETTY_PUBLIC_TOKEN": None,
    "BETTY_PRIVATE_TOKEN": None,
    "BETTY_CACHE_FLUSHER": None
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
