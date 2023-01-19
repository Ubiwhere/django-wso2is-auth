"""
Module to interact with the Django WSO2 token API
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests

from django_wso2is.conf import settings

logger = logging.getLogger(__name__)


def get_all_users() -> list[str]:
    """
    Returns all WSO2 users. The WSO2 identifier is based
    on the `ATTRIBUTE_MAPPING` value of `DJANGO_USER_LOOKUP_FIELD`.
    """
    from .utils import get_wso2_user_lookup_field

    response = requests.get(
        f"{settings.SERVER_URL}/scim2/Users",
        auth=(settings.ADMIN_USER_USERNAME, settings.ADMIN_USER_SECRET_KEY),
        verify=settings.VERIFY_SSL,
    )
    response.raise_for_status()
    # Get which field is used as remote identifier
    wso2_lookup = get_wso2_user_lookup_field()
    # Return list of users
    return [user.get(wso2_lookup) for user in response.json().get("Resources")]


@dataclass
class Token:
    """API to interact with WSO's identity server."""

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None

    def introspect(self):
        """Performs token introspection"""
        response = requests.post(
            f"{settings.SERVER_URL}/oauth2/introspect",
            data={"token": self.access_token},
            auth=(settings.ADMIN_USER_USERNAME, settings.ADMIN_USER_SECRET_KEY),
            verify=settings.VERIFY_SSL,
        )
        response.raise_for_status()
        return response.json()

    # Properties
    @property
    def is_active(self) -> bool:
        """
        Returns a boolean indicating if the current access token is active or not, by
        using token introspection endpoint.
        """
        return self.introspect()["active"]

    @property
    def user_info(self) -> dict:
        """
        Returns the user information.

        https://docs.wso2.com/display/IS450/OpenID+Connect+Basic+Client+Profile+with+WSO2+Identity+Server
        """

        response = requests.get(
            f"{settings.SERVER_URL}/scim2/Me",
            headers={"authorization": f"Bearer {self.access_token}"},
            verify=settings.VERIFY_SSL,
        )
        response.raise_for_status()
        return response.json()

    @property
    def user_id(self) -> Optional[str]:
        """
        Returns the WSO2 user id.
        """
        return self.user_info.get("id")

    @property
    def is_superuser(self) -> bool:
        """
        Check if token belongs to a user with superuser permissions.
        """

        if (settings.CLIENT_ADMIN_ROLE in self.client_roles) or (
            settings.GROUP_ADMIN_ROLE in self.group_roles
        ):
            return True

        return False

    @property
    def client_roles(self) -> list[str]:
        """
        Returns a list of the user roles.
        """
        return [
            sub["display"]
            for sub in self.user_info.get("roles", [])
            if "display" in sub
        ]

    @property
    def group_roles(self) -> list[str]:
        """
        Returns a list of the user group roles
        """
        return [
            sub["display"]
            for sub in self.user_info.get("groups", [])
            if "display" in sub
        ]

    @property
    def client_scopes(self) -> list[str]:
        """
        Returns the client scopes based on the access token.
        """
        return self.introspect()["scope"].split(" ")

    @classmethod
    def from_credentials(cls, username: str, password: str) -> Optional[Token]:
        """
        Creates a `Token` object from a set of user credentials.
        Returns `None` if authentication fails.
        """
        response = requests.request(
            "POST",
            f"{settings.SERVER_URL}/oauth2/token",
            auth=(settings.OAUTH_CLIENT_ID, settings.OAUTH_SECRET_KEY),
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": "internal_login openid",
            },
            verify=settings.VERIFY_SSL,
        )
        response.raise_for_status()
        response = response.json()
        return Token(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            id_token=response["id_token"],
        )

    @classmethod
    def from_access_token(cls, access_token: str) -> Optional[Token]:
        """
        Creates a `Token` object from an existing access token.
        Returns `None` if token is not active.
        """
        instance = cls(access_token=access_token)
        return instance if instance.is_active else None

    @classmethod
    def from_refresh_token(cls, refresh_token: str) -> Optional[Token]:
        """
        Creates a `Token` from the provided refresh token.
        """
        instance = cls(refresh_token=refresh_token)
        instance.refresh()
        return instance if instance.is_active else None

    def refresh(self) -> None:
        """
        Refreshes the `access_token` with `refresh_token`.

        Raises:
            KeycloakError: On Keycloak API errors
        """
        if self.refresh_token is None:
            return
        response = requests.request(
            "POST",
            f"{settings.SERVER_URL}/oauth2/token",
            auth=(settings.OAUTH_CLIENT_ID, settings.OAUTH_SECRET_KEY),
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            verify=settings.VERIFY_SSL,
        )
        response.raise_for_status()
        response = response.json()
        self.access_token = response["access_token"]
        self.refresh_token = response["refresh_token"]
        self.id_token = response["id_token"]
