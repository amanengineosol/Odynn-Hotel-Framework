from django.urls import path
from .views.airline import Airline
from .views.hotel import Hotel
# from .views.hotel_wrapper import HotelAsyncWrapperAPIView

urlpatterns= [
    # path('v2/hotel/', HotelAsyncWrapperAPIView.as_view(), name='HotelAsyncWrapperView'),
    path('airline/', Airline.as_view(), name='Airline'),
    path('hotel/', Hotel.as_view(), name='Hotel'),
    
]