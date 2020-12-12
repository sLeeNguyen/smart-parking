from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import CreateView
from .forms import RegisterForm
from .models import User


class RegisterView(CreateView):
    form_class = RegisterForm
    model = User

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        context = {
            'form': form
        }
        return render(request, template_name='', context=context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            instance = form.save()
            context = {
                'username': instance.username,
                'password': instance.password
            }
            return HttpResponseRedirect(reverse('core:login'))
        return render(request, template_name='register.html', context={'form': form})
