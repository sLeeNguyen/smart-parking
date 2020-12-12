from django.db import models
from django.utils.translation import gettext_lazy as _


class Device(models.Model):
    device_id = models.CharField(_('device id'),
                                 max_length=30,
                                 primary_key=True,
                                 unique=True,
                                 blank=False,
                                 null=False)
    device_name = models.CharField(_('device name'),
                                   max_length=100,
                                   default='')
    description = models.TextField(_('device description'),
                                   default='')
    position = models.CharField(_('device position'),
                                max_length=15,
                                unique=True)
    is_active = models.BooleanField(_('active'), default=False)
