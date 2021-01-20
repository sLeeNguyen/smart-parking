from django.db import models
from django.utils.translation import gettext_lazy as _


class Device(models.Model):
    device_id = models.CharField(_('device id'),
                                 max_length=50,
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
    slot_occupied = models.PositiveIntegerField(_("occupied position"),
                                                default=0)
    is_active = models.BooleanField(_('active'), default=False)

    def get_occupied(self):
        occupied_positions = []
        slot_occupied = int(self.slot_occupied)
        count = 0
        for i in range(6):
            if slot_occupied >> i & 1:
                occupied_positions.append(i + 1)
                count += 1
        return count, slot_occupied

    def to_occupied_array(self):
        slot_occupied = int(self.slot_occupied)
        occupied_array = []
        for i in range(6):
            occupied_array.append(slot_occupied >> i & 1)
        return occupied_array

    def set_slot(self, status, pos):
        pos = pos - 1
        slot_occupied = int(self.slot_occupied)
        if (slot_occupied >> pos & 1) == status:
            return False
        pre_pos = (slot_occupied >> (pos+1)) << (pos+1)
        post_pos = slot_occupied & ((1 << pos) - 1)
        self.slot_occupied = pre_pos | (status << pos) | post_pos
        return True
