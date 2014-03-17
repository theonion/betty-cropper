import json
from functools import wraps

from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils.decorators import available_attrs

from betty.authtoken.models import ApiToken


def forbidden():
    response_text = json.dumps({'message': 'Not authorized'})
    return HttpResponseForbidden(response_text, content_type="application/json")


def betty_token_auth(permissions):
    """
    Decorator to make a view only accept particular request methods.  Usage::

        @require_http_methods(["GET", "POST"])
        def my_view(request):
            # I can assume now that only GET or POST requests make it this far
            # ...

    Note that request methods should be in uppercase.
    """
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def inner(request, *args, **kwargs):
            if "betty.authtoken" in settings.INSTALLED_APPS:
                if request.user.is_anonymous():
                    if "HTTP_X_BETTY_API_KEY" not in request.META:
                        return forbidden()

                    api_key = request.META["HTTP_X_BETTY_API_KEY"]
                    try:
                        token = ApiToken.objects.get(public_token=api_key)
                    except ApiToken.DoesNotExist:
                        return forbidden()

                    request.user = token.get_user()
                if not request.user.has_perms(permissions):
                    return forbidden()

            return func(request, *args, **kwargs)
        return inner
    return decorator
