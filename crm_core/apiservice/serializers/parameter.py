from rest_framework import serializers


class AirlineParameterSerializer(serializers.Serializer):
    curency = serializers.CharField()
    source_iata = serializers.CharField(error_messages={
        'required': 'sourceIata value can not be null', 
        'blank': 'sourceIata value can not be null', 
        'null': 'sourceIata value can not be null'})
    destination_iata = serializers.CharField(error_messages={
        'required': 'destinationIata value can not be null', 
        'blank': 'destinationIata value can not be null', 
        'null': 'destinationIata value can not be null'})
    departure_date = serializers.DateField(error_messages={
        'required': 'departuredate value can not be null', 
        'blank': 'departuredate value can not be null', 
        'null': 'departuredate value can not be null'})
    return_date = serializers.DateField(required=False, allow_null=True)
    pos = serializers.CharField()
    num_of_adults = serializers.IntegerField(min_value=1, default=2)
    num_of_stops = serializers.IntegerField(min_value=0, default=0)
    is_round_trip = serializers.BooleanField(default=False)
    
    def validate_currency(self, value):
        if value != "USD":
            raise serializers.ValidationError("currency must be 'USD'")
        return value

    def validate_pos(self, value):
        if value != "US":
            raise serializers.ValidationError("pos must be 'US'")
        return value
    
    

class HotelParameterSerializer(serializers.Serializer):
    currency = serializers.CharField()
    hotel_id = serializers.CharField(error_messages={
        'required': 'hotel_id value can not be null', 
        'blank': 'hotel_id value can not be null', 
        'null': 'hotel_id value can not be null'})
    check_in_date = serializers.DateField(error_messages={
        'required': 'checkIn_date value can not be null', 
        'blank': 'checkIn_date value can not be null', 
        'null': 'checkIn_date value can not be null'})
    check_out_date = serializers.DateField(error_messages={
        'required': 'checkout_date value can not be null',
        'blank': 'numberOfStay value can not be null', 
        'null': 'numberOfStay value can not be null'})
    guest_count = serializers.IntegerField(min_value=1, error_messages={
        'required': 'numberOfStay value can not be null', 
        'blank': 'numberOfStay value can not be null', 
        'null': 'numberOfStay value can not be null'})
    pos = serializers.CharField()
    
    
    
    def validate_currency(self, value):
        if value != "USD":
            raise serializers.ValidationError("currency must be 'USD'")
        return value

    def validate_pos(self, value):
        if value != "US":
            raise serializers.ValidationError("pos must be 'US'")
        return value

    def validate(self, data):
        checkin = data.get("checkIn_date")
        checkout = data.get("checkout_date")
        if checkin and checkout and checkout <= checkin:
            raise serializers.ValidationError(
                "checkout_date must be at least 1 day after checkIn_date"
            )
        return data

