import logging

from django.conf import settings
from django.contrib.auth.models import Group

from django_cas_ng.backends import CASBackend
from users.models import ObjectPermission


logger = logging.getLogger('netbox.cas_authentication')


class CASGroupBackend(CASBackend):

    def user_can_authenticate(self, user):
        """Allow all users to try the CAS authentication."""
        # Needed in particular for users that tried to login before being authorized, for which there is already a user
        # record with active=False.
        return True

    def authenticate(self, request, ticket, service):
        """Hook authentication so that we can manipulate attributes and groups."""
        user = super().authenticate(request, ticket, service)
        if user:
            self._synchronize_attributes(user, request.session['attributes'])
        return user

    def bad_attributes_reject(self, request, username, attributes):
        """Hook aborting user creation if a group membership requirement is specified but not met."""
        if not settings.CAS_GROUP_REQUIRED:
            return False
        if not 'memberOf' in attributes:
            logger.error("CAS_GROUP_REQUIRED set but no `memberOf` attribute from CAS.")
            return True
        for group in settings.CAS_GROUP_REQUIRED:
            if group in attributes['memberOf']:
                return False
        logger.info(f"{username} is not a member of a required group and thus not created.")
        return True

    def _synchronize_attributes(self, user_obj, attributes):
        """
        Synchronize groups and flags based on attributes from CAS.
        """
        logger.debug("Synchronizing groups and flags")
        groups = []
        for group in attributes['memberOf']:
            # assign raw groups
            try:
                groups.append(Group.objects.get(name=group))
            except Group.DoesNotExist:
                logger.warning((f"Could not assign group {group} to CAS user {user_obj}:"
                                "Group not found"))

            # assign groups via group mappings
            if group in settings.CAS_GROUP_MAPPING:
                for netbox_group in settings.CAS_GROUP_MAPPING[group]:
                    try:
                        groups.append(Group.objects.get(name=netbox_group))
                    except Group.DoesNotExist:
                        logger.error((f"Could not assign mapped group {group}->{netbox_group} to "
                                      f"CAS user {user_obj}: Group not found"))

        user_obj.groups.clear()
        logger.debug(f"Cleared existing groups for CAS user {user_obj}")
        if groups:
            user_obj.groups.add(*groups)
            logger.debug(f"Assigned groups to CAS user {user_obj}: {groups}")

        # assign user flags based on which groups appear on the user
        usergroups = [group.name for group in user_obj.groups.all()]
        for flag, grouplist in settings.CAS_GROUP_ATTRIBUTE_MAPPING.items():
            if any(x in grouplist for x in usergroups):
                logger.info(f"Setting flag {flag} for CAS user {user_obj}")
                setattr(user_obj, flag, True)
            else:
                logger.info(f"Clearing flag {flag} for CAS user {user_obj}")
                setattr(user_obj, flag, False)

        user_obj.save()
