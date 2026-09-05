from django.urls import path

from . import views

app_name = 'cars'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('filters/count/', views.filter_count, name='filter_count'),
    path('cars/<slug:slug>/', views.car_detail, name='car_detail'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
]
