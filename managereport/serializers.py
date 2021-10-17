from django.db.models import fields
from rest_framework import serializers
from .models import Applicationlist

class ApplicationlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicationlist
        fields = '__all__'