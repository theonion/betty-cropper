from django.contrib.auth.models import AnonymousUser

from betty.authtoken.backends import BettyApiKeyBackend


class BettyApiKeyMiddleware(object):

    def process_request(self, request):
        if not "HTTP_X_BETTY_API_KEY" in request.META:
            return

        api_key = request.META["HTTP_X_BETTY_API_KEY"]
        backend = BettyApiKeyBackend()
        user = backend.authenticate(api_key=api_key)
        request.user = user or AnonymousUser()
        return
