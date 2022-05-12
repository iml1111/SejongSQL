from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Path, Form, File
from module.decorator import login_required, get_user
from module.environ import connect_to_environ, create_env, copy_env
from django_jwt_extended import jwt_required
from app_main.models import Class, Env, EnvBelongClass, TableBelongEnv
from app_main.serializer import EnvInEbcSrz, EnvSrz
from django.db.models import F
from uuid import uuid4
import shutil
import re
from module.async_queue import get_async_queue, freeze

class EnvView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        분반 소속 Env 반환 API
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
        
        envs = Env.objects.filter(
            envbelongclass__class_id=data['class_id']
        ).annotate(
            owner=F('user_id__id'),
            status=F('result'),
            share=F('envbelongclass__share')
        )
        envs_srz = EnvSrz(envs, many=True)

        return OK(envs_srz.data)    


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        분반 Env 생성 API
        SA, 교수, 조교 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Form('name', str),
                File('file'),
                Form('share', str, optional=True)
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
            query = data['file'].read().decode('utf-8')
        except:
            return FORBIDDEN("Incorrect sql file.")
        
        if data['share']:
            share = int(data['share'])
        else:
            share = 1

        q = get_async_queue(worker_num=3, qsize=100)
        q.add(freeze(create_env)(
            user=user,
            classes=classes,
            query=query,
            env_name=data['name'],
            file_name=data['file'].name,
            share=share,
            type='class'
        ))

        return CREATED()        


    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        특정 분반의 Env 삭제 API
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

        env = Env.objects.filter(
            id=data['env_id'],
            envbelongclass__class_id=data['class_id']
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")

        
        db = connect_to_environ()

        tbe = TableBelongEnv.objects.filter(env_id=data['env_id'])
        with db.cursor() as cursor:
            for table in tbe:
                cursor.execute(f"SET foreign_key_checks = 0;")
                cursor.execute(f"DROP TABLE {table.table_name};")
                cursor.execute(f"SET foreign_key_checks = 1;")  #foreign key 무시하고 테이블 삭제
            db.commit()

        env.delete()
        
        return NO_CONTENT   


class MyEnvView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        나의 소속 Env 반환 API
        """

        user = get_user(request)
        envs = Env.objects.filter(  #성공, 실패 상관없이 반환
            user_id=user.id,
            envbelongme__user_id=user.id
        ).annotate(
            owner=F('user_id'),
            status=F('result'),
            share=F('envbelongme__share')
        )
        envs_srz = EnvSrz(envs, many=True)
        return OK(envs_srz.data)        


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        나의 Env 생성 API
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Form('name', str),
                File('file'),
                Form('share', str, optional=True)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        try:
            query = data['file'].read().decode('utf-8')
        except:
            return FORBIDDEN("Incorrect sql file.")

        if data['share']:
            share = int(data['share'])
        else:
            share = 1

        q = get_async_queue(worker_num=3, qsize=100)
        q.add(freeze(create_env)(
            user=user,
            query=query,
            env_name=data['name'],
            file_name=data['file'].name,
            share=share,
            type='mine'
        ))

        return CREATED()    


    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        나의 Env 삭제 API
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('env_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        env = Env.objects.filter(
            id=data['env_id'],
            user_id=user.id,
            envbelongme__user_id=user.id
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")
        
        db = connect_to_environ()

        tbe = TableBelongEnv.objects.filter(env_id=data['env_id'])
        with db.cursor() as cursor:
            for table in tbe:
                cursor.execute(f"SET foreign_key_checks = 0;")
                cursor.execute(f"DROP TABLE {table.table_name};")
                cursor.execute(f"SET foreign_key_checks = 1;")  #foreign key 무시하고 테이블 삭제
            db.commit()

        env.delete()
        
        return NO_CONTENT   


class EnvCopyMeView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        나의 Env로 복사 API
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('env_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        env = Env.objects.filter(   #복사할 env
            id=data['env_id'],
            result='success'    #성공한 env만 복사
        ).filter(
            envbelongclass__share=1    #공유허가된 env만 복사 가능
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")
        
        q = get_async_queue(worker_num=3, qsize=100)
        q.add(freeze(copy_env)(
            env=env,
            user=user
        ))

        return CREATED()


class EnvCopyClassView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        분반 Env로 복사 API
        SA, 교수, 조교만 호출 가능
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

        env = Env.objects.filter(   #복사할 env
            id=data['env_id'],
            result='success'    #성공한 env만 복사
        ).filter(
            envbelongme__user_id=user.id,   #나의 env인지 확인
            envbelongme__share=1    #공유허가된 env만 복사 가능
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")
        
        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")

        q = get_async_queue(worker_num=3, qsize=100)
        q.add(freeze(copy_env)(
            env=env,
            user=user,
            classes=classes
        ))

        return CREATED()
