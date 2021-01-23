from django.urls import path

from . import views

app_name = 'core'
urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('car/', views.ListCarView.as_view(), name='car'),
    path('car/register/', views.CarRegisterView.as_view(), name='car-register'),
    path('check/in/', views.check_in, name='validate-license-number'),
    path('check/out/', views.check_out, name='validate-license-number'),
    path('parking/', views.ParkingView.as_view(), name='parking'),
]
