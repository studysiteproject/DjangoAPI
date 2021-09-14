from django.db.models import fields
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ['user_pw']
        # fields = '__all__'

class UserPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_pw']