"""Custom authentication class for Django Rest Framework."""
from typing import Union

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from django_wso2is import Token

from .utils import update_or_create_user


class BearerAuthentication(TokenAuthentication):
    """
    A custom token authentication class for WSO2.
    """

    # `keyword` refers to expected prefix in HTTP
    # Authentication header. Use the user-defined prefix
    keyword = "Bearer"

    def authenticate_credentials(self, access_token: str):
        """
        Overrides `authenticate_credentials` to provide custom
        WSO2 authentication for a given token in a request.
        """

        # Try to build a Token instance from the provided access token in request
        token: Union[Token, None] = Token.from_access_token(access_token)

        # Check for valid Token instance
        if not token:
            raise AuthenticationFailed

        # Update or create user
        user = update_or_create_user(token)

        return (user, token.access_token)
