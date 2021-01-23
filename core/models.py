from django.db import models
from django.utils import timezone

from users.models import Car, User


class ParkingHistory(models.Model):
    time_in = models.DateTimeField(auto_now_add=timezone.now)
    time_out = models.DateTimeField(blank=True, null=True)
    fees = models.PositiveIntegerField(blank=True, null=True)
    car = models.ForeignKey(to=Car, on_delete=models.CASCADE)
