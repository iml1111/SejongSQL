from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path, Form, File
from module.decorator import login_required, get_user
from django_jwt_extended import jwt_required
from app_main.models import User, Class, Env, EnvBelongClass, TableBelongEnv
from app_main.serializer import (
    ClassSrz,
    SearchUserSrz,
    UBCSrz,
    ClassInUbcSrz,
    EnvInEbcSrz
)
from django.db.models import F, Q
import sqlparse
import uuid


class EnvView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        분반 소속 Env 반환 API
        SA, 교수, 조교 호출 가능
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
            if not ubc.is_admin:
                return FORBIDDEN("student can't access.")
        
        envs = EnvBelongClass.objects.filter(
            class_id=data['class_id'],
            share=1     #공유 허가인 Env만 반환
        ).annotate(
            owner=F('env_id__user_id'),
            name=F('env_id__name'),
            updated_at=F('env_id__updated_at'),
            created_at=F('env_id__created_at')
        )

        envs_srz = EnvInEbcSrz(envs, many=True)
        return OK(envs_srz.data)


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        Env 생성 API
        SA, 교수, 조교 호출 가능
        """
        #인코딩, 용량체크를 통해  sql파일만 받도록. 이미지 파일을 강제로 sql파일로 받는 개같은 짓을 할 경우
        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Form('name', str),
                File('file'),
                Form('share', int, optional=True)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        """
        print(data['file'].name)   #파일 이름 추출
        ext = extract_ext(data['file'].name)   #파일 확장자 추출
        print(ext)
        print(data['file'].size)  #파일 사이즈 추출
        print(result.get_queries())
        print("---------------------------------------")
        print(result.get_tables())
        print("---------------------------------------")
        print(result.get_query_list(newline=False))
        """

        if not user.is_sa:
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:
                return FORBIDDEN("student can't access.")
        
        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")

        query = data['file'].read().decode('utf-8')
        
        result = SqlParser(query)

        env = Env(
            user_id=user,
            name=data['name'],
            file_name=data['file'].name
            #status 어떻게 하지?
        )
        env.save()

        ebc = EnvBelongClass(
            env_id=env,
            class_id=classes,
            share=data['share'] or None
        )
        ebc.save()

        for nickname, name in result.get_tables().items():
            tbe = TableBelongEnv(
                env_id=env,
                table_name=name,
                table_nickname=nickname
            )
            tbe.save()

        return CREATED()

    
    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        Env 삭제 API
        SA, 교수, 조교 호출 가능
        본인 Env만 삭제 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('env_id', int)
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

        env = Env.objects.filter(id=data['env_id'], user_id=user.id).first()
        if not env:
            return FORBIDDEN("can't find env.")

        env.delete()
        return NO_CONTENT


class EnvCopyView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        Env 복사 API
        SA, 교수, 조교 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('env_id', int)
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

        env = Env.objects.filter(id=data['env_id']).first()
        if not env:
            return FORBIDDEN("can't find env.")

        
        

#Env 생성, 삭제가 과연 관리자 전용인가?