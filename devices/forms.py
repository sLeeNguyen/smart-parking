from django import forms

from .models import Device


class DeviceAdminForm(forms.ModelForm):
    """
    A form for adding new device.
    """

    class Meta:
        model = Device
        fields = '__all__'
