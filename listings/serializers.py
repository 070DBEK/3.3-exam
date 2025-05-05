from rest_framework import serializers
from django.contrib.auth.models import User
from cars.serializers import CarSerializer
from users.serializers import UserSerializer
from .models import Listing, Image, PriceHistory, SavedListing, ComparisonList
from cars.models import Car


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['id', 'listing', 'image', 'is_primary', 'order', 'created_at']


class ListingSerializer(serializers.ModelSerializer):
    car = CarSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    primary_image = serializers.SerializerMethodField()
    car_id = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.all(), source='car', write_only=True
    )

    class Meta:
        model = Listing
        fields = [
            'id', 'car', 'seller', 'title', 'description', 'price', 'currency',
            'location', 'condition', 'is_negotiable', 'is_active', 'is_featured',
            'views_count', 'created_at', 'updated_at', 'expires_at', 'images',
            'primary_image', 'car_id'
        ]
        read_only_fields = ['seller', 'views_count', 'created_at', 'updated_at']

    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        return None

    def create(self, validated_data):
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = ['id', 'listing', 'price', 'currency', 'created_at']


class SavedListingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    listing = ListingSerializer(read_only=True)
    listing_id = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(), source='listing', write_only=True
    )

    class Meta:
        model = SavedListing
        fields = ['id', 'user', 'listing', 'created_at', 'listing_id']
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ComparisonListSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    listings = ListingSerializer(many=True, read_only=True)
    listing_ids = serializers.PrimaryKeyRelatedField(
        queryset=Listing.objects.all(), source='listings', write_only=True, many=True
    )

    class Meta:
        model = ComparisonList
        fields = ['id', 'user', 'name', 'listings', 'created_at', 'updated_at', 'listing_ids']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def create(self, validated_data):
        listings = validated_data.pop('listings', [])
        validated_data['user'] = self.context['request'].user
        comparison_list = ComparisonList.objects.create(**validated_data)
        comparison_list.listings.set(listings)
        return comparison_list
