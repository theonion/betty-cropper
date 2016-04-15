from django.utils.module_loading import import_string

from betty.conf.app import settings


def get_cache_flusher():
    if settings.BETTY_CACHE_FLUSHER:
        if callable(settings.BETTY_CACHE_FLUSHER):
            return settings.BETTY_CACHE_FLUSHER
        else:
            return import_string(settings.BETTY_CACHE_FLUSHER)
