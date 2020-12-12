from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('register-car/', views.CarView.as_view(), name='register-car'),
    path('validate-license/', views.check_license_number, name='validate-license-number')
]
