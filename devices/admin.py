from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Device
from .forms import DeviceAdminForm


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    form = DeviceAdminForm
    add_form = DeviceAdminForm
    list_display = ('device_id', 'device_name', 'position', 'is_active')
    list_filter = ('position', 'is_active')
