from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from taggit.managers import TaggableManager

from dcim.models import Interface
from extras.models import TaggedItem
from extras.utils import extras_features
from ipam.choices import *
from ipam.constants import *
from netbox.models import OrganizationalModel, PrimaryModel
from utilities.querysets import RestrictedQuerySet
from virtualization.models import VMInterface


__all__ = (
    'VLAN',
    'VLANGroup',
)


@extras_features('custom_fields', 'export_templates', 'webhooks')
class VLANGroup(OrganizationalModel):
    """
    A VLAN group is an arbitrary collection of VLANs within which VLAN IDs and names must be unique.
    """
    name = models.CharField(
        max_length=100
    )
    slug = models.SlugField(
        max_length=100
    )
    site = models.ForeignKey(
        to='dcim.Site',
        on_delete=models.PROTECT,
        related_name='vlan_groups',
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=200,
        blank=True
    )

    objects = RestrictedQuerySet.as_manager()

    csv_headers = ['name', 'slug', 'site', 'description']

    class Meta:
        ordering = ('site', 'name', 'pk')  # (site, name) may be non-unique
        unique_together = [
            ['site', 'name'],
            ['site', 'slug'],
        ]
        verbose_name = 'VLAN group'
        verbose_name_plural = 'VLAN groups'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('ipam:vlangroup_vlans', args=[self.pk])

    def to_csv(self):
        return (
            self.name,
            self.slug,
            self.site.name if self.site else None,
            self.description,
        )

    def get_next_available_vid(self):
        """
        Return the first available VLAN ID (1-4094) in the group.
        """
        vlan_ids = VLAN.objects.filter(group=self).values_list('vid', flat=True)
        for i in range(1, 4095):
            if i not in vlan_ids:
                return i
        return None


@extras_features('custom_fields', 'custom_links', 'export_templates', 'webhooks')
class VLAN(PrimaryModel):
    """
    A VLAN is a distinct layer two forwarding domain identified by a 12-bit integer (1-4094). Each VLAN must be assigned
    to a Site, however VLAN IDs need not be unique within a Site. A VLAN may optionally be assigned to a VLANGroup,
    within which all VLAN IDs and names but be unique.

    Like Prefixes, each VLAN is assigned an operational status and optionally a user-defined Role. A VLAN can have zero
    or more Prefixes assigned to it.
    """
    site = models.ForeignKey(
        to='dcim.Site',
        on_delete=models.PROTECT,
        related_name='vlans',
        blank=True,
        null=True
    )
    group = models.ForeignKey(
        to='ipam.VLANGroup',
        on_delete=models.PROTECT,
        related_name='vlans',
        blank=True,
        null=True
    )
    vid = models.PositiveSmallIntegerField(
        verbose_name='ID',
        validators=[MinValueValidator(1), MaxValueValidator(4094)]
    )
    name = models.CharField(
        max_length=64
    )
    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='vlans',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=50,
        choices=VLANStatusChoices,
        default=VLANStatusChoices.STATUS_ACTIVE
    )
    role = models.ForeignKey(
        to='ipam.Role',
        on_delete=models.SET_NULL,
        related_name='vlans',
        blank=True,
        null=True
    )
    description = models.CharField(
        max_length=200,
        blank=True
    )
    tags = TaggableManager(through=TaggedItem)

    objects = RestrictedQuerySet.as_manager()

    csv_headers = ['site', 'group', 'vid', 'name', 'tenant', 'status', 'role', 'description']
    clone_fields = [
        'site', 'group', 'tenant', 'status', 'role', 'description',
    ]

    class Meta:
        ordering = ('site', 'group', 'vid', 'pk')  # (site, group, vid) may be non-unique
        unique_together = [
            ['group', 'vid'],
            ['group', 'name'],
        ]
        verbose_name = 'VLAN'
        verbose_name_plural = 'VLANs'

    def __str__(self):
        return self.display_name or super().__str__()

    def get_absolute_url(self):
        return reverse('ipam:vlan', args=[self.pk])

    def clean(self):
        super().clean()

        # Validate VLAN group
        if self.group and self.group.site != self.site:
            raise ValidationError({
                'group': "VLAN group must belong to the assigned site ({}).".format(self.site)
            })

    def to_csv(self):
        return (
            self.site.name if self.site else None,
            self.group.name if self.group else None,
            self.vid,
            self.name,
            self.tenant.name if self.tenant else None,
            self.get_status_display(),
            self.role.name if self.role else None,
            self.description,
        )

    @property
    def display_name(self):
        return f'{self.name} ({self.vid})'

    def get_status_class(self):
        return VLANStatusChoices.CSS_CLASSES.get(self.status)

    def get_interfaces(self):
        # Return all device interfaces assigned to this VLAN
        return Interface.objects.filter(
            Q(untagged_vlan_id=self.pk) |
            Q(tagged_vlans=self.pk)
        ).distinct()

    def get_vminterfaces(self):
        # Return all VM interfaces assigned to this VLAN
        return VMInterface.objects.filter(
            Q(untagged_vlan_id=self.pk) |
            Q(tagged_vlans=self.pk)
        ).distinct()