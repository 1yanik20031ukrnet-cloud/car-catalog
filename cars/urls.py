from django.urls import path

from . import views

app_name = 'cars'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('cars/<slug:slug>/', views.car_detail, name='car_detail'),
]
