from django.utils import timezone
from rest_framework import serializers
from .models import (
    User, EnvBelongTable, Warning,
    Problem, ProblemGroup, UserSolveProblem,
    UserBelongAuth, WarningBelongProblem
)
from django.db.models import F, Q


class UserSrz(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'sejong_id', 'name', 'role', 'created_at', 'updated_at', 'pw_updated_at')


class SearchUserSrz(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'sejong_id', 'name', 'major')


class UserRoleSrz(serializers.ModelSerializer):
    class Meta:
        model = UserBelongAuth
        fields = ('id', 'user_id', 'role', 'result')


class UserInClassSrz(serializers.Serializer):
    id = serializers.CharField(max_length=100)
    sejong_id = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    type = serializers.CharField(max_length=100)
    created_at = serializers.DateTimeField()


class SAClassSrz(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    semester = serializers.CharField(max_length=100)
    comment = serializers.CharField(max_length=1000)
    activate = serializers.BooleanField(default=1)
    type = serializers.CharField(max_length=100)
    prof = serializers.SerializerMethodField()
    pgroup = serializers.SerializerMethodField()

    def get_pgroup(self, obj):
        pgroup = obj.problemgroup_set.values('id', 'name').order_by('id')
        return pgroup


    def get_prof(self, obj):
        prof = obj.userbelongclass_set.filter(
            type='prof'
        ).annotate(
            prof_id=F("user_id__id"),
            sejong_id=F("user_id__sejong_id"),
            name=F("user_id__name"),
            major=F("user_id__major")
        ).values('prof_id', 'sejong_id', 'name', 'major').first()

        result = {
            'id': prof['prof_id'],
            'sejong_id': prof['sejong_id'],
            'name': prof['name'],
            'major': prof['major']
        }
        return result
    

class ClassSrz(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    semester = serializers.CharField(max_length=100)
    comment = serializers.CharField(max_length=1000)
    activate = serializers.BooleanField(default=1)
    type = serializers.CharField(max_length=100)
    prof = serializers.SerializerMethodField()
    pgroup = serializers.SerializerMethodField()


    def get_pgroup(self, obj):
        if obj.type in ('prof', 'ta'):
            pgroup = obj.problemgroup_set.values('id', 'name').order_by('id')
            return pgroup
        else:
            pgroup = obj.problemgroup_set.filter(
                Q(exam=1) | #시험모드이거나
                (
                    (Q(activate_start=None) | Q(activate_start__lt=timezone.now())) &
                    (Q(activate_end=None) | Q(activate_end__gt=timezone.now()))
                )   #활성화일 때만 반환
            ).values(
                'id',
                'name'
            ).order_by('id')
            return pgroup


    def get_prof(self, obj):
        prof = obj.userbelongclass_set.filter(
            type='prof'
        ).annotate(
            prof_id=F("user_id__id"),
            sejong_id=F("user_id__sejong_id"),
            name=F("user_id__name"),
            major=F("user_id__major")
        ).values('prof_id', 'sejong_id', 'name', 'major').first()

        result = {
            'id': prof['prof_id'],
            'sejong_id': prof['sejong_id'],
            'name': prof['name'],
            'major': prof['major']
        }
        return result


class ProblemGroupSrz(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    problem_cnt = serializers.IntegerField()
    solve_cnt = serializers.IntegerField()
    exam = serializers.BooleanField()
    activate = serializers.BooleanField()
    activate_start = serializers.DateTimeField()
    activate_end = serializers.DateTimeField()


class CertainPgroupSrz(serializers.ModelSerializer):
    class Meta:
        model = ProblemGroup
        fields = ('id', 'name', 'comment', 'exam', 'activate', 'activate_start', 'activate_end')


class ClassEnvSrz(serializers.Serializer):
    id = serializers.IntegerField()
    owner = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=100)
    updated_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    status = serializers.CharField(max_length=200)
    table = serializers.SerializerMethodField()


    def get_table(self, obj):
        table = EnvBelongTable.objects.filter(
            env_id=obj.id
        ).values_list('table_name')
        return [key[0] for key in table]


class MyEnvSrz(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    updated_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField()
    status = serializers.CharField(max_length=200)
    table = serializers.SerializerMethodField()


    def get_table(self, obj):
        table = EnvBelongTable.objects.filter(
            env_id=obj.id
        ).values_list('table_name')
        return [key[0] for key in table]


class ProblemSrz(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=100)
    content = serializers.CharField(max_length=20000)


class ProblemInGroupSrz(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=100)
    status = serializers.CharField(max_length=100)
    problem_warnings = serializers.IntegerField()
    user_warnings = serializers.IntegerField()


class MyProblemSrz(serializers.ModelSerializer):
    usp_id = serializers.IntegerField()
    accuracy = serializers.BooleanField()
    
    class Meta:
        model = Problem
        fields = ('id', 'usp_id', 'title', 'accuracy')


class USPSrz(serializers.Serializer):
    problem_id = serializers.IntegerField()
    title = serializers.CharField(max_length=100)
    content = serializers.CharField(max_length=20000)
    query = serializers.CharField(max_length=1000)
    accuracy = serializers.BooleanField()


class AllInProblemSrz(serializers.Serializer):
    answer = serializers.CharField(max_length=100)
    timelimit = serializers.FloatField()
    title = serializers.CharField(max_length=100)
    content = serializers.CharField(max_length=100)
    warnings = serializers.SerializerMethodField()

    def get_warnings(self, obj):
        warnings = WarningBelongProblem.objects.filter(
            p_id=obj.id
        ).annotate(
            warning=F('warning_id__id'),
            name=F('warning_id__name'),
            content=F('warning_id__content')
        ).values('warning', 'name', 'content')

        result = []
        for warning in warnings:
            result.append({
                'id': warning['warning'],
                'name': warning['name'],
                'content': warning['content']
            })
        return result


class StatusSrz(serializers.ModelSerializer):
    usp_id = serializers.IntegerField()
    sejong_id = serializers.CharField(max_length=100)
    pg_name = serializers.CharField(max_length=100)
    p_title = serializers.CharField(max_length=100)
    p_created_at = serializers.DateTimeField()
    access = serializers.BooleanField()

    class Meta:
        model = UserSolveProblem
        fields = ('usp_id', 'user_id', 'sejong_id', 'pg_name', 'p_id', 'p_title', 'p_created_at', 'access')


class WarningSrz(serializers.ModelSerializer):
    class Meta:
        model = Warning
        fields = '__all__'


class UserWarningSrz(serializers.Serializer):
    usp_id = serializers.IntegerField()
    name = serializers.CharField(max_length=100)
    content = serializers.CharField(max_length=100)