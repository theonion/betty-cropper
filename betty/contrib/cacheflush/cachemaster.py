# Sample BETTY_CACHE_FLUSHER integration using Onion's CacheMaster service
#
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests

from betty.conf.app import settings

logger = __import__('logging').getLogger(__name__)


def flush(paths):

    urls = [urljoin(settings.BETTY_IMAGE_URL, path) for path in paths]

    resp = requests.post(settings.CACHEMASTER_URL, data=dict(urls=urls))
    if not resp.ok:
        logger.error('CacheMaster flush failed: %s %s %s',
                     resp.request.url,
                     resp.status_code,
                     resp.reason)
    return resp
