from rest_framework import serializers
from ..models.request import Request 
from django.contrib.auth import get_user_model
from .parameter_serializer_mapping import PARAMETER_SERIALIZER_MAP
from gatekeeper.models.company_info import Company
from crawler.models import Crawler

class UUIDToCompanyPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    def to_internal_value(self, data):
        # If data looks like email, try to get User by email
        
            try:
                company = Company.objects.get(uuid=data)
                return company
            except company.DoesNotExist:
                raise serializers.ValidationError(f"Customer with uuid '{data}' does not exist.")

class RequestSerializer(serializers.ModelSerializer):
    client_id = UUIDToCompanyPrimaryKeyField(queryset=Company.objects.all())
    class Meta:
        model = Request
        fields = '__all__'
        

    def validate(self, data):
        if data.get("retry_count") != 2:
            raise serializers.ValidationError(
                {"retry_count": "retry_count must always be 2"}
            )
        domain = data.get('domain_name')
        param = data.get('parameter')
        param_serializer_class = PARAMETER_SERIALIZER_MAP.get(domain)
        if not param_serializer_class:
            raise serializers.ValidationError(f"Unsupported domain: {domain}")
        param_serializer = param_serializer_class(data=param)
        param_serializer.is_valid(raise_exception=True)
        return data
    
    def validate_site_name(self, value):
        if not Crawler.objects.filter(crawler_name=value).exists():
            raise serializers.ValidationError("This site_name is not recognized.")
        return value