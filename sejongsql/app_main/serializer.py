from rest_framework import serializers
from .models import User, Class, UserBelongClass


class UserSrz(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'role', 'created_at', 'updated_at', 'pw_updated_at')


class ClassSrz(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ('name', 'semester', 'comment', 'activate')


class UserBelongClassSrz(serializers.ModelSerializer):
    class Meta:
        model = UserBelongClass
        fields =('user_id','user_id__name')
    
    def get_my_class(self, obj):
        return {
            'name': obj.class_id.name,
            'semester': obj.class_id.semester,
            'comment': obj.class_id.comment,
            'activate': obj.class_id.activate,
            'type': obj.type,
        }