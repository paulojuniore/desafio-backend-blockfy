from rest_framework import serializers
from .models import PixMessage

class PixMessageSerializer(serializers.ModelSerializer):
  class Meta:
    model = PixMessage
    fields = '__all__'