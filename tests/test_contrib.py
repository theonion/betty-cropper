import json

from httmock import all_requests, HTTMock, response, urlmatch
from mock import patch
import requests

from betty.contrib.cacheflush import cachemaster


def test_cachemaster_flush(settings):
    settings.BETTY_IMAGE_URL = 'http://onion.local'
    settings.CACHEMASTER_URLS = ['http://cachemaster.local/flush']

    @all_requests
    def success(url, request):
        assert request.url == 'http://cachemaster.local/flush'
        assert request.method == 'POST'
        assert json.loads(request.body.decode('utf-8')) == {
            'urls': ['http://onion.local/path/one',
                     'http://onion.local/two/']
        }
        return response(200, 'YAY TEST WORKED')

    with HTTMock(success):
        resp = cachemaster.flush(['/path/one', '/two/'])

    assert resp.text == 'YAY TEST WORKED'  # Ensures we actually hit the mock


def test_cachemaster_first_flush_fails(settings):
    settings.BETTY_IMAGE_URL = 'http://onion.local'
    settings.CACHEMASTER_URLS = ['http://cachemaster1.local/flush',
                                 'http://cachemaster2.local/flush',
                                 'http://cachemaster3.local/flush']

    @urlmatch(netloc='cachemaster1.local', path='/flush')
    def error_500(url, request):
        return response(500, request=request)  # Simulate failed request

    @urlmatch(netloc='cachemaster2.local', path='/flush')
    def error_connection(url, request):
        raise requests.ConnectionError

    @urlmatch(netloc='cachemaster3.local', path='/flush', method='POST')
    def success(url, request):
        return response(200, 'YAY TEST WORKED')

    with HTTMock(error_500, error_connection, success):
        with patch('betty.contrib.cacheflush.cachemaster.logger') as mock_log:
            resp = cachemaster.flush(['/path/one'])
            # Two errors
            assert 2 == (mock_log.error.call_count + mock_log.exception.call_count)

    assert resp.text == 'YAY TEST WORKED'  # Ensures we actually hit the mock


def test_cachemaster_all_fail(settings):
    settings.CACHEMASTER_URLS = ['http://cachemaster1.local/flush',
                                 'http://cachemaster2.local/flush']

    @all_requests
    def error_500(url, request):
        return response(500)

    with HTTMock(error_500):
        with patch('betty.contrib.cacheflush.cachemaster.logger') as mock_log:
            resp = cachemaster.flush(['/path/one'])
            assert 2 == mock_log.error.call_count

    assert resp is None
