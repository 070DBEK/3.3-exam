from django.db import models
from django.utils.translation import gettext_lazy as _


class Make(models.Model):
    name = models.CharField(max_length=50)
    country = models.CharField(max_length=50, blank=True)
    logo = models.ImageField(upload_to='makes/', blank=True, null=True)

    def __str__(self):
        return self.name


class Model(models.Model):
    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.make.name} {self.name}"


class BodyType(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='body_types/', blank=True, null=True)

    def __str__(self):
        return self.name


class Feature(models.Model):
    CATEGORY_CHOICES = (
        ('comfort', _('Comfort')),
        ('safety', _('Safety')),
        ('interior', _('Interior')),
        ('exterior', _('Exterior')),
        ('multimedia', _('Multimedia')),
    )

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.name


class Car(models.Model):
    FUEL_TYPE_CHOICES = (
        ('petrol', _('Petrol')),
        ('diesel', _('Diesel')),
        ('hybrid', _('Hybrid')),
        ('electric', _('Electric')),
        ('gas', _('Gas')),
    )

    TRANSMISSION_CHOICES = (
        ('manual', _('Manual')),
        ('automatic', _('Automatic')),
        ('semi_auto', _('Semi-Automatic')),
    )

    DRIVE_TYPE_CHOICES = (
        ('front', _('Front Wheel Drive')),
        ('rear', _('Rear Wheel Drive')),
        ('full', _('Full Wheel Drive')),
    )

    make = models.ForeignKey(Make, on_delete=models.CASCADE, related_name='cars')
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='cars')
    year = models.PositiveIntegerField()
    body_type = models.ForeignKey(BodyType, on_delete=models.SET_NULL, null=True, related_name='cars')
    fuel_type = models.CharField(max_length=10, choices=FUEL_TYPE_CHOICES)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_CHOICES)
    color = models.CharField(max_length=50)
    mileage = models.PositiveIntegerField()
    engine_size = models.FloatField(help_text=_('Engine size in liters'))
    power = models.PositiveIntegerField(help_text=_('Power in horsepower'))
    drive_type = models.CharField(max_length=10, choices=DRIVE_TYPE_CHOICES)
    features = models.ManyToManyField(Feature, blank=True, related_name='cars')
    vin = models.CharField(max_length=17, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.make.name} {self.model.name} {self.year}"
