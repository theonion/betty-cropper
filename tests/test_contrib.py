try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

from httmock import all_requests, HTTMock, response
from betty.contrib.cacheflush import cachemaster


def test_cachemaster_flush(settings):

    settings.BETTY_IMAGE_URL = 'http://onion.local'
    settings.CACHEMASTER_URL = 'http://cachemaster.local/flush'

    @all_requests
    def response_content(url, request):
        assert request.url == 'http://cachemaster.local/flush'
        assert request.method == 'POST'
        assert parse_qs(request.body) == {'urls': ['http://onion.local/path/one',
                                                   'http://onion.local/two/']}
        return response(200, 'YAY TEST WORKED')

    with HTTMock(response_content):
        resp = cachemaster.flush(['/path/one',
                                  '/two/'])

    assert resp.text == 'YAY TEST WORKED'  # Ensures we actually hit the mock
