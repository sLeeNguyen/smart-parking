from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('car/', views.CarRegisterView.as_view(), name='car'),
    path('validate-license/', views.check_license_number, name='validate-license-number')
]
