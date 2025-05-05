from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Review
from users.serializers import UserSerializer
from listings.serializers import ListingSerializer
from listings.models import Listing


class ReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)
    reviewed_user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    reviewed_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='reviewed_user', write_only=True
    )
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(), source='listing', write_only=True, required=False
    )

    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'reviewed_user', 'listing', 'rating', 'comment',
            'created_at', 'reviewed_user_id', 'listing_id'
        ]
        read_only_fields = ['reviewer', 'created_at']

    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)
