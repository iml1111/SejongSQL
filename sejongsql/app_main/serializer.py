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


class UBCASrz(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    semester = serializers.CharField(max_length=200)
    comment = serializers.CharField(max_length=200)
    activate = serializers.BooleanField(default=1)
    type = serializers.CharField(max_length=200)
    is_prof = serializers.BooleanField()

    def get_is_prof(self):
        return type == 'prof'