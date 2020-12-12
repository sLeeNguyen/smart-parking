from django import forms
from django.utils.translation import gettext_lazy as _

from .models import User, Car


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'email']

    def clean_confirm_password(self):
        # Check that two passwords entries match
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data['confirm-password']
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError(_("Passwords don't match"))


class UserDetailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
        exclude = ['password']


class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']


class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = ['car_name', 'description', 'license_plate_number', 'owner']
