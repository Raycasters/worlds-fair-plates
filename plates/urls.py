from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('plates/', views.plate_list, name='plate_list'),
    path('plates/<pk>/', views.plate_details, name='plate_details'),
    path('listings/', views.listings, name='listings'),
    path('manage/', views.manage, name='manage'),
]
