import json
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


class LoginView(View):

    def get(self, request, *args, **kwargs):
        redirect_to = request.GET.get('next', '')
        return render(request, template_name='login.html', context={'next': redirect_to})

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if not username or not password:
            context = {
                'error': 'username and password are required.'
            }
            return render(request, template_name='', context=context)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # redirect to a success page
            if request.GET:
                redirect_to = request.GET.get('next', '')
            if redirect_to:
                return HttpResponseRedirect(redirect_to=redirect_to)
            else:
                return HttpResponseRedirect(reverse("core:home"))
        else:
            context = {
                'error': 'username and password are incorrect.'
            }
            return render(request, template_name='home.html', context=context)


def logout(request):
    logout(request)
    # redirect to home page
    return render(request, template_name='home.html')


class CarView(LoginRequiredMixin, CreateView, DeleteView):
    login_url = '/login/'
    redirect_field_name = 'next'
    form_class = CarForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form
        }
        return render(request, template_name='car_register.html', context=context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(owner=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse(''))
        return render(request, template_name='car_register.html', context={'form': form})

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
