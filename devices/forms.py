import uuid

from django import forms

from .models import Device


class DeviceAdminForm(forms.ModelForm):
    """
    A form for adding new device.
    """
    device_id = forms.CharField(
        label="Device ID",
        widget=forms.TextInput(attrs={
            "placeholder": "Auto generate"
        }),
        required=False
    )

    class Meta:
        model = Device
        fields = ['device_id', 'device_name', 'description', 'position', 'is_active']

    def clean_device_id(self):
        device_id = self.instance.device_id
        if not device_id:
            device_id = str(uuid.uuid1())
        print("Created new device with id: %s" % device_id)
        return device_id
