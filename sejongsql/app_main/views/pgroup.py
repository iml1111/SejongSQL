from rest_framework.views import APIView
from module.response import (
    OK, NO_CONTENT, BAD_REQUEST,
    FORBIDDEN, CREATED, NOT_FOUND
)
from module.validator import Validator, Json, Path
from module.decorator import login_required, get_user
from app_main.models import Class, ProblemGroup, Problem, UserBelongClass
from app_main.serializer import ProblemGroupSrz, CertainPgroupSrz
from datetime import datetime
from django.db.models import Count
from django_jwt_extended import jwt_required


class PgroupView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 분반의 문제집 목록 반환 API
        학생일 경우, 활성화된 문제집만 반환
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
            ])
        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")

        if user.is_sa or ubc.is_admin:  #관리자
            pgroups = ProblemGroup.objects.filter(
                class_id=data['class_id'],
            ).annotate(
                problem_cnt=Count('problem__id')
            )
        else:   #학생
            pgroups = ProblemGroup.objects.filter(
                class_id=data['class_id'],
                class_id__activate=True,    #활성화된 분반인지
                activate=True,  #활성화인 문제집인지
            ).annotate(
                problem_cnt=Count('problem__id'),
            )

        for pgroup in pgroups:
            problems = Problem.objects.filter(
                    pg_id=pgroup.id,
                    usersolveproblem__user_id=user.id,
                    usersolveproblem__accuracy=1
                ).annotate(
                    solve_cnt=Count('id')
                ).values()
            pgroup.solve_cnt = len(problems)
        
        pgroup_srz = ProblemGroupSrz(pgroups, many=True)
        return OK(pgroup_srz.data)      


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        문제집 생성 API
        SA, 교수, 조교 호출 가능
        activate_start 와 end 는 null 가능.
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Json('name', str),
                Json('comment', str),
                Json('exam', int),
                Json('activate', int),
                Json('activate_start', str, optional=True),
                Json('activate_end', str, optional=True),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")

        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")

        try:
            if data['activate_start']:
                datetime.strptime(data['activate_start'],"%Y-%m-%d %H:%M:%S")
            if data['activate_end']:
                datetime.strptime(data['activate_end'],"%Y-%m-%d %H:%M:%S")
        except: 
            return BAD_REQUEST("Incorrect date format.")

        pgroup = ProblemGroup(
            class_id = classes,
            name = data['name'],
            comment = data['comment'],
            exam = data['exam'],
            activate = data['activate'],
            activate_start = data['activate_start'] or None,
            activate_end = data['activate_end'] or None
        )
        pgroup.save()

        return CREATED()

    
    @jwt_required()
    @login_required()
    def put(self, request, **path):
        """
        문제집 수정 API
        SA, 교수, 조교만 호출 가능
        activate_start 와 end 는 null 가능.
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int),
                Json('name', str),
                Json('comment', str),
                Json('exam', int),
                Json('activate', int),
                Json('activate_start', str, optional=True),
                Json('activate_end', str, optional=True),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")
        
        pgroup = ProblemGroup.objects.filter(
            id=data['pgroup_id'],
            class_id=data['class_id']
        ).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")

        try:
            if data['activate_start']:
                datetime.strptime(data['activate_start'],"%Y-%m-%d %H:%M:%S")
            if data['activate_end']:
                datetime.strptime(data['activate_end'],"%Y-%m-%d %H:%M:%S")
        except: 
            return BAD_REQUEST("Incorrect date format.")

        pgroup.name = data['name']
        pgroup.comment = data['comment']
        pgroup.exam = data['exam']
        pgroup.activate = data['activate']
        pgroup.activate_start = data['activate_start'] or None
        pgroup.activate_end = data['activate_end'] or None
        pgroup.save()

        return CREATED()


    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        문제집 삭제 API
        SA, 교수, 조교만 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:
                return FORBIDDEN("student can't access.")
        
        pgroup = ProblemGroup.objects.filter(
            id=data['pgroup_id'],
            class_id=data['class_id']
        ).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")

        pgroup.delete()

        return NO_CONTENT


class CertainPgroupView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 문제집 반환 API
        학생은 활성화 체크
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('pgroup_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:
            check_user = UserBelongClass.objects.filter(
                user_id=user.id,
                class_id__problemgroup=data['pgroup_id'],
            ).first()
            if not check_user:
                return FORBIDDEN("can't find class or pgroup.")
        
        if user.is_sa or check_user.is_admin:   #관리자
            pgroup = ProblemGroup.objects.filter(
                id=data['pgroup_id']
            ).first()
        else:   #학생
            pgroup = ProblemGroup.objects.filter(
                id=data['pgroup_id'],
                class_id__activate=True,    #활성화된 분반인지
                activate=True,  #활성화된 문제집인지
            ).first()
        if not pgroup:
            return NOT_FOUND

        pgroup_srz = CertainPgroupSrz(pgroup)
        return OK(pgroup_srz.data)