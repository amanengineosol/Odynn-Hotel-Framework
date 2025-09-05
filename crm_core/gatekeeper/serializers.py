# gatekeeper/serializers.py
from rest_framework import serializers
from .models.user import User


class ClientOpsCreationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'confirm_password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        password = data['password']
        if password != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        company_info = self.context['company']
        max_ops = company_info.limit
        current_ops = User.objects.filter(client_id=company_info, user_type='client_ops').count()
        if current_ops >= max_ops:
            raise serializers.ValidationError(
                f"Limit reached: {max_ops} client_ops allowed. Contact admin to increase."
            )
        return data

    def create(self, validated_data):
        client_admin_instance = self.context['company']
        email = validated_data['email']
        full_name = validated_data['full_name']
        password = validated_data['password']
        user = User.objects.create_user(
            email=email,
            password = password,
            full_name=full_name,
            user_type='client_ops',
            client_id=client_admin_instance,
        )
        return user
