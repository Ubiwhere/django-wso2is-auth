"""Utility function's module."""

import logging

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from jsonpath_ng import parse

from django_wso2is import Token
from django_wso2is.conf import settings

from .signals import user_authenticated

logger = logging.getLogger(__name__)


def update_or_create_user(token: Token):
    """Given a `Token` instance it checks if updates or creates the user
    in the local database."""

    lookup_field: str = get_django_user_lookup_field()
    # Get the user model
    User = get_user_model()
    payload: dict = get_mapped_fields_values(token)
    # Extract lookup field from payload
    lookup_value = payload.pop(lookup_field, None)

    if lookup_value is None:
        raise ImproperlyConfigured(
            f"The lookup field `{lookup_field}` has value `None`."
            f"Is `{lookup_field}` in `ATTRIBUTE_MAPPING`?"
        )

    # Check for superuser permissions
    if token.is_superuser:
        payload["is_staff"] = True
        payload["is_superuser"] = True

    user, _ = User.objects.update_or_create(
        **{lookup_field: lookup_value},
        defaults=payload,
    )
    # Dispatch signal
    user_authenticated.send(
        sender=None,
        user=user,
        token=token,
    )

    return user


def get_django_user_lookup_field() -> str:
    """Returns the field that should be used for unique user lookup.
    First the `DJANGO_USER_LOOKUP_FIELD` setting is used. It not specified,
    the auth model `USERNAME_FIELD` is used, with a fallback to `username`
    attribute."""
    return settings.DJANGO_USER_LOOKUP_FIELD or getattr(
        get_user_model(), "USERNAME_FIELD", "username"
    )


def get_wso2_user_lookup_field() -> str:
    """Returns the field that should be used for unique user lookup
    on remote WSO2 server."""
    local_lookup = get_django_user_lookup_field()
    try:
        return settings.ATTRIBUTE_MAPPING[local_lookup]
    except KeyError:
        raise ImproperlyConfigured(
            f"Local user lookup field is specified as {local_lookup}. However,"
            "this field is not present in `ATTRIBUTE_MAPPING`. Please map this field to "
            "a WSO2 attribute"
        )


def get_mapped_fields_values(token: Token) -> dict:
    """Given a list of django's user field names it tries to find the field's values
    from the provided `token` instance (based on `token.user_info`)
    and `ATTRIBUTE_MAPPING` setting."""

    # Get user information from token instance
    user_info = token.user_info
    values = {}
    for django_field, wso2_attribute in settings.ATTRIBUTE_MAPPING.items():
        try:
            val = parse(wso2_attribute).find(user_info)[0].value
        except IndexError:
            val = None
        values[django_field] = val

    return values
