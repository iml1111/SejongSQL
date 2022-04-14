from rest_framework import serializers
from .models import User, ProblemGroup
from .models import SamplePost, SampleComment


class SamplePostSrz(serializers.ModelSerializer):
    class Meta:
        model = SamplePost
        fields = '__all__'


class SampleCommentSrz(serializers.ModelSerializer):
    class Meta:
        model = SampleComment
        fields = '__all__'


class UserSrz(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'role', 'created_at', 'updated_at', 'pw_updated_at')


class ProblemGroupSrz(serializers.ModelSerializer):
    class Meta:
        model = ProblemGroup
        fields = ('name', 'exam', 'activate_start', 'activate_end')