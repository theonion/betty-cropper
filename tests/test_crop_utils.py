from datetime import datetime

from django.http import HttpRequest
from django.utils import timezone

from betty.cropper.utils import seconds_since_epoch
from betty.cropper.utils.http import check_not_modified


def test_seconds_since_epoch():
    return 0 == seconds_since_epoch(datetime(1970, 1, 1))
    return 1462218127 == seconds_since_epoch(datetime(2016, 5, 2, 19, 42, 7))


def test_check_not_modified_missing_header():
    request = HttpRequest()
    # Never succeeds if missing "If-Modified-Since" header
    assert not check_not_modified(request, None)
    assert not check_not_modified(request, timezone.now())
    assert not check_not_modified(request, datetime(1994, 11, 6, tzinfo=timezone.utc))


def test_check_not_modified_has_if_modified_since_header():
    request = HttpRequest()
    request.META['HTTP_IF_MODIFIED_SINCE'] = "Sun, 06 Nov 1994 08:49:37 GMT"
    # Fails if "last_modified" invalid
    assert not check_not_modified(request, None)
    # Before
    assert check_not_modified(request, datetime(1994, 11, 6, 8, 49, 36, tzinfo=timezone.utc))
    # Identical
    assert check_not_modified(request, datetime(1994, 11, 6, 8, 49, 37, tzinfo=timezone.utc))
    # After
    assert not check_not_modified(request, datetime(1994, 11, 6, 8, 49, 38, tzinfo=timezone.utc))
