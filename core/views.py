import json
import re

from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import DeleteView, CreateView, ListView
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin

from users.forms import CarForm
from users.models import Car


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


def logout(request):
    logout(request)
    # redirect to home page
    return render(request, template_name='home.html')


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
    template_name = ''
    model = Car
    queryset = Car.objects.all()

    def get_queryset(self):
        queryset = self.queryset.filter(owner=self.request.user)
        return queryset


@csrf_exempt
def check_license_number(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            license_number = data['license_number']
        except KeyError:
            return JsonResponse(data={
                        'status': 'fail',
                        'message': 'Body must have license_number field'
                }, status=404)

        if Car.objects.filter(license_plate_number=license_number).exists():
            return JsonResponse(data={
                'status': 'success'
            })
    return JsonResponse(data={
        'status': 'fail',
        'message': 'License plate number does not exists'
    })
