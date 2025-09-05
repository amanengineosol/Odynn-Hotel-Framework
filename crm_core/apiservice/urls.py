from django.urls import path
from .views.airline import Airline
from .views.hotel import Hotel

urlpatterns= [
    path('airline/', Airline.as_view(), name='Airline'),
    path('hotel/', Hotel.as_view(), name='Hotel'),
]