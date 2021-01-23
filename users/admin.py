from django.contrib import admin
from django.conf import settings
from . import models
from .forms import CarForm


admin.site.register(models.User)


@admin.register(models.Car)
class CarAdmin(admin.ModelAdmin):
    form = CarForm
    list_display = ('id', 'car_name', 'license_plate_number', 'owner',)
    list_filter = ('owner',)

    # In admin site, the manager can not have add, change, delete permissions
    # with Car model. Therefore, we must disable those permissions, just only
    # have view permissions
    # But in the develop environment, we enable it to be easily tested
    def has_add_permission(self, request):
        """
        Disable add permission in production
        """
        if settings.DEVELOP_ENVIRONMENT:
            return super().has_add_permission(request)
        return False

    def has_change_permission(self, request, obj=None):
        """
        Disable change permission in production
        """
        if settings.DEVELOP_ENVIRONMENT:
            return super().has_change_permission(request)
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Disable delete permission in production
        """
        if settings.DEVELOP_ENVIRONMENT:
            return super().has_delete_permission(request)
        return False
