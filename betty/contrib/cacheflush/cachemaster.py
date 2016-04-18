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

    if not hasattr(settings, 'CACHEMASTER_URLS') or not isinstance(settings.CACHEMASTER_URLS, list):
        raise KeyError('Invalid/missing setting: "CACHEMASTER_URLS" - list of string URLS')

    urls = [urljoin(settings.BETTY_IMAGE_URL, path) for path in paths]

    # Try multiple URLS (for redundancy)
    for idx, cm_url in enumerate(settings.CACHEMASTER_URLS, start=1):
        try:
            resp = requests.post(cm_url, json=dict(urls=urls))
            if resp.ok:
                return resp
            else:
                logger.error('CacheMaster flush failed (%s/%s): %s %s %s %s',
                             idx,
                             len(settings.CACHEMASTER_URLS),
                             cm_url,
                             urls,
                             resp.status_code,
                             resp.reason)
        except requests.RequestException:
            logger.exception('CacheMaster flush failed (%s/%s): %s %s',
                             idx,
                             len(settings.CACHEMASTER_URLS),
                             cm_url,
                             urls)
