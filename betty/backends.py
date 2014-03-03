from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
User = get_user_model()


class BettyApiKeyBackend(ModelBackend):
    def authenticate(self, api_key=None):
        try:
            user = User.objects.get(api_key=api_key)
            return user
        except User.DoesNotExist:
            return None
