from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import CreateView
from .forms import RegisterForm
from .models import User


class RegisterView(CreateView):
    form_class = RegisterForm
    model = User

    # def get(self, request, *args, **kwargs):
    #     form = self.form_class()
    #     context = {
    #         'form': form
    #     }
    #     return render(request, template_name='sign_up.html', context=context)
    #
    # def post(self, request, *args, **kwargs):
    #     form = self.form_class(request.POST)
    #     if form.is_valid():
    #         instance = form.save()
    #         context = {
    #             'username': instance.username,
    #             'password': instance.password
    #         }
    #         return HttpResponseRedirect(reverse('core:login'))
    #     return render(request, template_name='sign_up.html.html', context={'form': form})

    def get(self, request, *args, **kwargs):
        return render(request, template_name='sign_up.html')

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        data = {'status': 'success'}
        if self.get_queryset().filter(email=email).exists():
            data = {'status': 'failed', 'msg': 'Email was used'}
        if password != confirm_password:
            data = {'status': 'failed', 'msg': 'Confirm password failed'}
        if data["status"] == "success":
            self.model.objects.create_user(username=name, email=email, password=password)
        return JsonResponse(data)
