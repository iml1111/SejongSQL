from rest_framework import serializers
from .models import User, Class, UserBelongClass


class UserSrz(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'role', 'created_at', 'updated_at', 'pw_updated_at')

class SearchUserSrz(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name')

class ClassSrz(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ('name', 'semester', 'comment', 'activate')

class UBCSrz(serializers.ModelSerializer):
    classes = ClassSrz(source='class_id')
    class Meta:
        model = UserBelongClass
        fields = ('classes', 'type')