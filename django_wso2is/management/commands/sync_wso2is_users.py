import logging as log

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q

from django_wso2is.token import get_all_users
from django_wso2is.utils import get_django_user_lookup_field


class Command(BaseCommand):
    help = "Synchronize users with WSO2is by deleting local users that do not exist remotely"

    def handle(self, *args, **options):
        # Get a list of all remote users
        remote_users = get_all_users()
        # Delete all users that exist locally but do not exist remotely
        number_deletions, _ = (
            get_user_model()
            .objects.filter(
                ~Q(**{f"{get_django_user_lookup_field()}__in": remote_users})
            )
            .delete()
        )

        log.info(
            f"Removed {number_deletions} users that do not exist in WSO2 identity server."
        )
