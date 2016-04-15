from betty.cropper.flush import get_cache_flusher


def mock_flusher(paths):
    pass


def test_get_cache_flusher_string(settings):
    settings.BETTY_CACHE_FLUSHER = 'tests.test_flush.mock_flusher'
    assert mock_flusher == get_cache_flusher()


def test_get_cache_flusher_callable(settings):
    settings.BETTY_CACHE_FLUSHER = mock_flusher
    assert mock_flusher == get_cache_flusher()
