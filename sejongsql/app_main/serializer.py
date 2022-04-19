from rest_framework import serializers
from .models import (
    User,
    Class,
    UserBelongClass,
    ProblemGroup,
    TableBelongEnv
)
from django.db.models import F


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


class ClassInUbcSrz(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    semester = serializers.CharField(max_length=100)
    comment = serializers.CharField(max_length=1000)
    activate = serializers.BooleanField(default=1)
    type = serializers.CharField(max_length=100)


class ProblemGroupSrz(serializers.ModelSerializer):
    class Meta:
        model = ProblemGroup
        fields = ('id', 'name', 'exam', 'activate_start', 'activate_end')


class EnvInEbcSrz(serializers.Serializer):
    id = serializers.IntegerField()
    owner = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    updated_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    table = serializers.SerializerMethodField()

    def get_table(self, obj):
        table = TableBelongEnv.objects.filter(
            env_id=obj.env_id
        ).annotate(
            name=F('table_nickname')
        )
        return table


class EnvSrz(serializers.Serializer):
    id = serializers.IntegerField()
    owner = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    updated_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    table = serializers.SerializerMethodField()

    def get_table(self, obj):
        table = TableBelongEnv.objects.filter(
            env_id=obj.id
        ).annotate(
            name=F('table_nickname')
        )
        return table
        