"""
Module containing custom errors.
"""


class WSO2MissingSettingError(Exception):
    """
    Raised when a given Django WSO2 setting(s) is missing.
    """

    def __init__(self, setting: str):
        super().__init__(
            (
                f"The following settings are missing: '{setting}' "
                "Please add them in 'WSO2IS_CONFIG' inside Django settings"
            )
        )
