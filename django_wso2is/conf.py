"""
Module to interact with django settings
"""
import re
from dataclasses import dataclass, field
from typing import Optional

from django.conf import settings as django_settings


@dataclass
class Settings:
    """
    Django WSO2 settings container
    """

    SERVER_URL: str
    # The ID of this client
    OAUTH_CLIENT_ID: str
    # The secret for this confidential client
    OAUTH_SECRET_KEY: str
    # The name of the admin role for the client
    ADMIN_USER_USERNAME: str
    ADMIN_USER_SECRET_KEY: str
    CLIENT_ADMIN_ROLE: str
    GROUP_ADMIN_ROLE: str
    VERIFY_SSL: bool = False
    DJANGO_USER_LOOKUP_FIELD: Optional[str] = None
    ATTRIBUTE_MAPPING: dict = field(
        default_factory=lambda: dict(
            username="userName",
        )
    )

    def __post_init__(self) -> None:

        # Make sure "SERVER_URL" don't contain any
        # trailing slash
        self.SERVER_URL = self.SERVER_URL.rstrip("/")


# Get wso2 configs from django
__configs = django_settings.WSO2IS_CONFIG
# Filter out configs with `None` as values
__configs = {
    k: v
    for k, v in __configs.items()
    if v is not None and k in Settings.__annotations__.keys()
}
try:
    # The exported settings object
    settings = Settings(**__configs)

except TypeError as e:
    import django_wso2is.errors as errors

    if "required positional argument" in str(e):
        # Get missing variables with regex
        missing_required_vars = re.findall("'([^']*)'", str(e))
        raise errors.WSO2MissingSettingError(" / ".join(missing_required_vars)) from e
    else:
        raise e
