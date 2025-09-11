from django.urls import path
from .views.hotel import Hotel

urlpatterns= [
    path('hotel/', Hotel.as_view(), name='Hotel'),
]