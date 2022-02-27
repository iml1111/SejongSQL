from rest_framework import serializers
from .models import SamplePost, SampleComment


class SamplePostSrz(serializers.ModelSerializer):
    class Meta:
        model = SamplePost
        fields = '__all__'


class SampleCommentSrz(serializers.ModelSerializer):
    class Meta:
        model = SampleComment
        fields = '__all__'