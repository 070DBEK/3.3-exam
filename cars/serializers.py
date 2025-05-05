from rest_framework import serializers
from .models import Make, Model, BodyType, Feature, Car


class MakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Make
        fields = ['id', 'name', 'country', 'logo']


class ModelSerializer(serializers.ModelSerializer):
    make = MakeSerializer(read_only=True)
    make_id = serializers.PrimaryKeyRelatedField(
        queryset=Make.objects.all(), source='make', write_only=True
    )
    class Meta:
        model = Model
        fields = ['id', 'name', 'make', 'make_id']


class BodyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BodyType
        fields = ['id', 'name', 'image']


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'name', 'category']


class CarSerializer(serializers.ModelSerializer):
    make = MakeSerializer(read_only=True)
    model = ModelSerializer(read_only=True)
    body_type = BodyTypeSerializer(read_only=True)
    features = FeatureSerializer(many=True, read_only=True)
    make_id = serializers.PrimaryKeyRelatedField(
        queryset=Make.objects.all(), source='make', write_only=True
    )
    model_id = serializers.PrimaryKeyRelatedField(
        queryset=Model.objects.all(), source='model', write_only=True
    )
    body_type_id = serializers.PrimaryKeyRelatedField(
        queryset=BodyType.objects.all(), source='body_type', write_only=True, required=False
    )
    feature_ids = serializers.PrimaryKeyRelatedField(
        queryset=Feature.objects.all(), source='features', write_only=True, many=True, required=False
    )

    class Meta:
        model = Car
        fields = [
            'id', 'make', 'model', 'year', 'body_type', 'fuel_type', 'transmission',
            'color', 'mileage', 'engine_size', 'power', 'drive_type', 'features',
            'vin', 'created_at', 'updated_at', 'make_id', 'model_id', 'body_type_id', 'feature_ids'
        ]
