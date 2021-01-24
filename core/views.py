import json
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DeleteView, CreateView, ListView
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin

from core.models import ParkingHistory
from devices.models import Device
from users.forms import CarForm
from users.models import Car

from elasticsearch_client import es as elasticsearch
from core.utils import client_timezone, get_client_timezone


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
    queryset = Car.objects.all()

    def get(self, request, *args, **kwargs):
        list_cars = self.get_queryset()
        list_histories = ParkingHistory.objects.filter(car__owner=request.user)
        if list_histories:
            list_histories = list_histories.order_by('-time_in')
        context = {"list_cars": list_cars, "list_histories": list_histories}
        return render(request, template_name=self.template_name, context=context)

    def get_queryset(self):
        queryset = self.queryset.filter(owner=self.request.user)
        return queryset


class CarHistoryView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'
    template_name = 'car_history.html'

    def get(self, request, car_id):
        print(car_id)
        car = get_object_or_404(Car, pk=car_id)
        list_histories = ParkingHistory.objects.filter(car=car)
        if list_histories:
            list_histories = list_histories.order_by('-time_in')
        context = {"list_histories": list_histories}
        return render(request, template_name=self.template_name, context=context)


@csrf_exempt
def check_in(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            license_number = data['license_number']
        except (json.decoder.JSONDecodeError, KeyError):
            return JsonResponse(data={
                        'status': 'fail',
                        'code': 1,
                        'message': 'Body must have license_number field'
                }, status=404)

        cars = Car.objects.filter(license_plate_number=license_number)
        if cars.exists():
            # check license already in parking or not
            try:
                ParkingHistory.objects.get(car=cars[0], time_out__isnull=True, fees__isnull=True)
                return JsonResponse(data={
                    'status': 'fail',
                    'code': 3,
                    'message': 'Fraud detection: the car with the license number %s already in parking' % license_number
                })
            except ParkingHistory.DoesNotExist:
                history = ParkingHistory.objects.create(car=cars[0])
                elasticsearch.index_parking_history(id=history.id,
                                                    car_id=history.car.id,
                                                    user_id=history.car.owner.id,
                                                    time_in=history.time_in)
                return JsonResponse(data={
                    'status': 'success'
                })
        else:
            return JsonResponse(data={
                'status': 'fail',
                'code': 2,
                'message': 'License plate number does not exists'
            })
    return JsonResponse(data={
        'status': 'fail'
    })


@csrf_exempt
def check_out(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            license_number = data['license_number']
        except (json.decoder.JSONDecodeError, KeyError):
            return JsonResponse(data={
                'status': 'fail',
                'code': 1,
                'message': 'Body must have license_number field'
            }, status=404)

        cars = Car.objects.filter(license_plate_number=license_number)
        if cars.exists():
            try:
                history = ParkingHistory.objects.get(car=cars[0], time_out__isnull=True, fees__isnull=True)
                history.time_out = timezone.now()
                history.fees, hours = calc_fees(time_in=history.time_in, time_out=history.time_out)
                history.save()
                elasticsearch.update_parking_history_time_out(id=history.id,
                                                              time_out=history.time_out,
                                                              fees=history.fees)
                return JsonResponse(data={
                    'status': 'success',
                    'fees': history.fees,
                    'time_in': client_timezone(history.time_in).strftime("%d/%m/%Y %H:%M:%S"),
                    'time_out': client_timezone(history.time_out).strftime("%d/%m/%Y %H:%M:%S"),
                    'duration': hours
                })
            except ParkingHistory.DoesNotExist:
                return JsonResponse(data={
                    'status': 'fail',
                    'code': 3,
                    'message': 'Fraud detection: the car with the license number %s not in parking' % license_number
                })
        else:
            return JsonResponse(data={
                'status': 'fail',
                'code': 2,
                'message': 'License plate number does not exists'
            })
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


class ParkingAnalysisView(LoginRequiredMixin, View):
    login_url = '/login/'
    redirect_field_name = 'next'

    def get(self, request):
        begin_time, end_time = self._get_time()
        # analysis parking history from elasticsearch
        analyze_data = elasticsearch.analysis_parking_history(begin_time=begin_time,
                                                              end_time=end_time,
                                                              timezone=get_client_timezone(request))
        in_analysis = analyze_data["aggregations"]["in_analysis"]
        out_analysis = analyze_data["aggregations"]["out_analysis"]
        in_labels = []
        out_labels = []
        in_datasets = []
        out_datasets = []
        in_total = in_analysis["doc_count"]
        in_buckets = in_analysis["group_by_hour"]["buckets"]
        out_total = out_analysis["doc_count"]
        out_buckets = out_analysis["group_by_hour"]["buckets"]
        in_max = out_max = 0

        if in_buckets:
            pre = int(in_analysis["group_by_hour"]["buckets"][0]["key"])
            for bucket in in_analysis["group_by_hour"]["buckets"]:
                next_hour = int(bucket["key"])
                if pre + 1 < next_hour:
                    for h in range(pre + 1, next_hour):
                        in_labels.append(str(h) + ":00")
                        in_datasets.append(0)
                pre = next_hour
                in_labels.append(bucket["key"] + ":00")
                in_datasets.append(bucket["doc_count"])
                in_max = max(in_max, bucket["doc_count"])
        if out_buckets:
            pre = int(in_analysis["group_by_hour"]["buckets"][0]["key"])
            for bucket in out_analysis["group_by_hour"]["buckets"]:
                next_hour = int(bucket["key"])
                if pre + 1 < next_hour:
                    for h in range(pre + 1, next_hour):
                        out_labels.append(str(h) + ":00")
                        out_datasets.append(0)
                pre = next_hour
                out_labels.append(bucket["key"] + ":00")
                out_datasets.append(bucket["doc_count"])
                out_max = max(out_max, bucket["doc_count"])

        if not in_labels:
            in_labels.append("00:00")
            in_datasets.append(0)
        if not out_labels:
            out_labels.append("00:00")
            out_datasets.append(0)
        response = {
            "in": {
                "labels": in_labels,
                "datasets": in_datasets,
                "total": in_total,
                "max": in_max,
            },
            "out": {
                "labels": out_labels,
                "datasets": out_datasets,
                "total": out_total,
                "max": out_max,
            }
        }
        print(response)
        return JsonResponse(status=200, data=response)

    def _get_time(self):
        time = self.request.GET["key_time"]
        begin_time = None
        end_time = None
        if time.lower() == "month":
            now = client_timezone(timezone.now())
            begin_time = now - timezone.timedelta(days=now.day-1)
            end_time = now
        elif time.lower() == "week":
            now = client_timezone(timezone.now())
            begin_time = now - timezone.timedelta(days=now.weekday())
            end_time = begin_time + timezone.timedelta(days=6)
        elif time.lower() == "today":
            begin_time = end_time = client_timezone(timezone.now())
        elif time.lower() == "yesterday":
            now = client_timezone(timezone.now())
            begin_time = end_time = now - timezone.timedelta(days=1)
        return begin_time, end_time


def calc_fees(time_in, time_out):
    BASE_FEE = 5000
    FEES_PER_HOUR = 10000
    duration = time_out - time_in
    hours = duration.days * 24 + duration.seconds / 3600
    return BASE_FEE + int(hours * FEES_PER_HOUR), hours
