from .parameter import AirlineParameterSerializer, HotelParameterSerializer


PARAMETER_SERIALIZER_MAP = {
    'airline': AirlineParameterSerializer,
    'hotel': HotelParameterSerializer,
}
