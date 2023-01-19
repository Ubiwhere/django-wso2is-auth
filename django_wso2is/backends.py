from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from django_wso2is import Token

from .utils import update_or_create_user


class WSO2isAuthenticationBackend(ModelBackend):
    """Django's authentication backend for WSO2 Identity Server."""

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Authenticates a user by credentials, and
        updates their information (first name, last name, email).
        If user does not exist it is created with appropriate permissions.
        Parameters
        ----------
        username: str
            WSO2 username.
        password: str
            WSO2 password.
        """

        if not (username and password):
            return

        # Create token from the provided credentials and check if
        # credentials were valid
        token: Optional[Token] = Token.from_credentials(username, password)

        # Check for non-existing or inactive token
        if not token:
            # credentials were not valid
            return
        return update_or_create_user(token)
