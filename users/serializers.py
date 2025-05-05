from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Dealer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'user_type', 'phone', 'avatar', 'location', 'rating', 'created_at']


class DealerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Dealer
        fields = [
            'id', 'user', 'company_name', 'description', 'logo', 'website',
            'address', 'is_verified', 'rating', 'created_at', 'updated_at'
        ]
