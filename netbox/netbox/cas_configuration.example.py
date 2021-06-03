#
# Django-cas-ng settings
# See https://djangocas.dev/docs/latest/configuration.html
#
# This setting is required if the authenticator in the configuration.py
# is set to 'django_cas_ng.backends.CASBackend' or 'netbox.cas_authentication.CASGroupBackend'
# which enable the CAS authenticator.
#
# CAS_SERVER_URL
#
# Please see the above URL for additional settings for the CAS authenticators.
#

#
# Group aware CAS settings
#  These are not part of the default django-cas-ng library, but an additional authenticator
#  which supports synchronizing groups from memberOf attribute provided by CAS.
#
# CAS_GROUP_MAPPING - assigns groups in Netbox based on groups passed from CAS
#   Format: {'group-from-memberOf': ('netboxGroup', ...), ...}
#
# CAS_GROUP_ATTRIBUTE_MAPPING - assigns attributes based on assigned groups
#   Format: {'attribute': ('netboxGroup', ...), ...}
#   Example: {'is_staff': ('staffGroup',)}
#   - if the user is member of staffGroup (in netbox) it will set is_staff True (otherwise False)
#
# CAS_GROUP_REQUIRED - early-stops adding user if memberOf group is not present
#   Format: ('group-from-memberOf',...)
