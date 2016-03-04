from django.contrib.auth.models import AnonymousUser
from .auth import ApiToken


class BettyApiKeyMiddleware(object):

    def process_request(self, request):
        if "HTTP_X_BETTY_API_KEY" in request.META:
            api_key = request.META["HTTP_X_BETTY_API_KEY"]
            try:
                token = ApiToken.objects.get(public_token=api_key)
            except ApiToken.DoesNotExist:
                request.user = AnonymousUser()
            else:
                request.user = token.get_user()
