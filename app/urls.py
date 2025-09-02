from django.urls import path
from . import views

urlpatterns = [
    path('', views.generate_itinerary_view, name='generate_itinerary'),
]