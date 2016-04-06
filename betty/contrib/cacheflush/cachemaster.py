# Sample BETTY_CACHE_FLUSHER integration using Onion's CacheMaster service
#
import requests

from betty.conf.app import settings

logger = __import__('logging').getLogger(__name__)


def flush(urls):
    resp = requests.post(settings.CACHEMASTER_URL, data=dict(urls=urls))
    if not resp.ok:
        logger.error('CacheMaster flush failed: %s %s %s',
                     resp.request.url,
                     resp.status_code,
                     resp.reason)
    return resp
