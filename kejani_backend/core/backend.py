"""
Custom authentication backend that authenticates using email instead of username.
Required because Django's default ModelBackend passes credentials as 'username'
internally, but our User model uses email as USERNAME_FIELD.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """Authenticate against email + password."""

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        # Accept either 'email' kwarg or 'username' kwarg (SimpleJWT passes 'username')
        lookup_email = email or username
        if not lookup_email or not password:
            return None

        try:
            user = User.objects_all.get(email=lookup_email.lower())
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
