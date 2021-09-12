from rest_framework import serializers
from .models import Refresh

class RefreshSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refresh
        fields = '__all__'