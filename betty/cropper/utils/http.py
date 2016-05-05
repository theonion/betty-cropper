from django.utils.http import parse_http_date_safe

from betty.cropper.utils import seconds_since_epoch


def check_not_modified(request, last_modified):
    """Handle 304/If-Modified-Since

    With Django v1.9.5+ could just use "django.utils.cache.get_conditional_response", but v1.9 is
    not supported by "logan" dependancy (yet).
    """

    if_modified_since = parse_http_date_safe(request.META.get('HTTP_IF_MODIFIED_SINCE'))
    return (last_modified and
            if_modified_since and
            seconds_since_epoch(last_modified) <= if_modified_since)
