from django.contrib.auth.models import AnonymousUser

from betty.backends import BettyApiKeyBackend


def get_user(request):
    if not hasattr(request, '_cached_user'):
        user = None
        try:
            api_key = request.META["HTTP_X_BETTY_API_KEY"]
        except KeyError:
            pass
        else:
            user = BettyApiKeyBackend.authenticate(api_key=api_key)
        request._cached_betty_user = user or AnonymousUser()
    return request._cached_betty_user


class BettyApiKeyMiddleware(object):

    def process_request(self, request):
        if not "HTTP_X_BETTY_API_KEY" in request.META:
            return
    
        api_key = request.META["HTTP_X_BETTY_API_KEY"]
        backend = BettyApiKeyBackend()
        user = backend.authenticate(api_key=api_key)
        if user:
            request.user = user
        return
