import json
import re

from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DeleteView, CreateView, ListView
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin

from core.consumers import send_parking_state_data
from core.models import ParkingHistory
from devices.models import Device
from users.forms import CarForm
from users.models import Car
from elasticsearch_client import es as elasticsearch


class HomeView(View):

    def get(self, request, *args, **kwargs):
        return render(request, template_name='home.html')


class LoginView(View):

    def get(self, request, *args, **kwargs):
        redirect_to = request.GET.get('next', '')
        return render(request, template_name='sign_in.html', context={'next': redirect_to})

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        if not email or not password:
            context = {
                'error': 'email and password are required.',
                'email': email,
                'password': password
            }
            return render(request, template_name='sign_in.html', context=context)
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            # redirect to a success page
            redirect_to = None
            if request.GET:
                redirect_to = request.GET.get('next', '')
            if redirect_to:
                return HttpResponseRedirect(redirect_to=redirect_to)
            else:
                return HttpResponseRedirect(reverse("core:home"))
        else:
            context = {
                'error': 'email and password are incorrect.',
                'email': email,
                'password': password
            }
            return render(request, template_name='sign_in.html', context=context)


def logout_view(request):
    logout(request)
    # redirect to home page
    return redirect(reverse('core:home'))


class CarRegisterView(LoginRequiredMixin, CreateView, DeleteView):
    login_url = '/login/'
    redirect_field_name = 'next'
    form_class = CarForm
    model = Car

    def get(self, request, *args, **kwargs):
        return render(request, template_name='car_register.html')

    def post(self, request, *args, **kwargs):
        car_name = request.POST.get('car-name')
        license_plate = request.POST.get('license-plate', '').upper()
        description = request.POST.get('description')

        pattern = re.compile("[0-9]{2}[A-Z][0-9]{5}([0-9])?")
        response = {'status': 'success'}
        if self.get_queryset().filter(license_plate_number=license_plate).exists():
            response = {'status': 'failed', 'msg': 'License plate number already exists'}
        if not pattern.match(license_plate):
            response = {'status': 'failed', 'msg': 'License plate number is invalid'}
        if response['status'] == 'success':
            self.model.objects.create(car_name=car_name,
                                      license_plate_number=license_plate,
                                      description=description,
                                      owner=request.user)
        return JsonResponse(data=response)

    def delete(self, request, *args, **kwargs):
        pass


class ListCarView(LoginRequiredMixin, ListView):
    login_url = '/login/'
    redirect_field_name = 'next'
    template_name = 'car_management.html'
    model = Car
    queryset = Car.objects.all()

    def get(self, request, *args, **kwargs):
        return render(request, template_name=self.template_name)

    def get_queryset(self):
        queryset = self.queryset.filter(owner=self.request.user)
        return queryset


@csrf_exempt
def check_in(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            license_number = data['license_number']
        except KeyError:
            return JsonResponse(data={
                        'status': 'fail',
                        'message': 'Body must have license_number field'
                }, status=404)

        cars = Car.objects.filter(license_plate_number=license_number)
        if cars.exists():
            history = ParkingHistory.objects.create(car=cars[0])
            elasticsearch.index_parking_history(id=history.id,
                                                car_id=history.car.id,
                                                user_id=history.car.user.id,
                                                time_in=history.time_in)
            return JsonResponse(data={
                'status': 'success'
            })
    return JsonResponse(data={
        'status': 'fail',
        'message': 'License plate number does not exists'
    })


@csrf_exempt
def check_out(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            license_number = data['license_number']
        except KeyError:
            return JsonResponse(data={
                        'status': 'fail',
                        'message': 'Body must have license_number field'
                }, status=404)

        cars = Car.objects.filter(license_plate_number=license_number)
        if cars.exists():
            try:
                history = ParkingHistory.objects.get(car=cars[0], time_out__isnull=True, fees__isnull=True)
                history.time_out = timezone.now()
                history.fees = calc_fees(time_in=history.time_in, time_out=history.time_out)
                history.save()
                elasticsearch.update_parking_history_time_out(id=history.id,
                                                              time_out=history.time_out,
                                                              fees=history.fees)
            except ParkingHistory.DoesNotExist:
                pass
    return JsonResponse(data={
        'status': 'fail',
    })


class ParkingView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'
    template_name = "parking_position.html"

    def get(self, request):
        parking_map = {}
        for device in Device.objects.all():
            if device.is_active:
                parking_map[device.position] = device.to_occupied_array()
            else:
                parking_map[device.position] = [-1]*6
        print(parking_map)
        context = {
            "map": parking_map
        }
        return render(request, template_name=self.template_name, context=context)


def calc_fees(time_in, time_out):
    BASE_FEE = 5000
    FEES_PER_HOUR = 10000
    duration = time_out - time_in
    hours = duration.days * 24 + duration.seconds / 3600
    return BASE_FEE + int(hours * FEES_PER_HOUR)
