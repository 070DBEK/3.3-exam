from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Message
from users.serializers import UserSerializer
from listings.serializers import ListingSerializer
from listings.models import Listing


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='receiver', write_only=True
    )
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(), source='listing', write_only=True
    )

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'receiver', 'listing', 'content', 'is_read',
            'created_at', 'receiver_id', 'listing_id'
        ]
        read_only_fields = ['sender', 'is_read', 'created_at']

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)
