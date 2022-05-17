from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Path, Form, File
from module.decorator import login_required, get_user
from module.environ import get_db, create_env
from django_jwt_extended import jwt_required
from app_main.models import Class, Env, EnvBelongClass
from app_main.serializer import ClassEnvSrz, MyEnvSrz
from django.db.models import F
from module.async_queue import get_async_queue, freeze
from django.conf import settings


class EnvView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        분반에 연결된 env 목록 반환 API
        SA, 교수, 조교만 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int)
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
        
        envs = Env.objects.filter(  #성공, 실패 상관없이 반환
            envbelongclass__class_id=data['class_id']
        ).annotate(
            owner=F("user_id__id"),
            status=F("result")
        )
        
        envs_srz = ClassEnvSrz(envs, many=True)
        return OK(envs_srz.data)

    
    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        내 env 생성 API
        SA, 교수, 조교만 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Form('name', str),
                File('file')
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

        if Env.objects.filter(
            envbelongclass__class_id=data['class_id'],  #같은 분반 내에
            name=data['name'],   #같은 이름의 env가 있는지 확인
            result='success'    #성공한 env인 경우
        ).exists():
            return FORBIDDEN("same env name is already created.")
        elif Env.objects.filter(
                envbelongclass__class_id=data['class_id'],
                name=data['name']
            ).exists():

            Env.objects.filter(
                envbelongclass__class_id=data['class_id'],
                name=data['name']
            ).first().delete()
            
        try:
            query = data['file'].read().decode('utf-8')
        except:
            return FORBIDDEN("Incorrect sql file.")

        q = get_async_queue(
            worker_num=getattr(settings, 'ASYNC_QUEUE_WORKER', None),
            qsize=getattr(settings, 'ASYNC_QUEUE_SIZE', None),
        )
        q.add(freeze(create_env)(
            user=user,
            classes=classes,
            query=query,
            env_name=data['name'],
        ))
        
        return CREATED()


    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        내 env 삭제 API
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
            user_id=user.id
            ).first()
        if not env:
            return FORBIDDEN("can't find env.")

        db = get_db()
        cursor = db.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS {env.db_name};")
        db.close()

        env.delete()
        return NO_CONTENT


class ConnectEnvView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        내 env 목록 반환 API
        """

        user = get_user(request)
        envs = Env.objects.filter(
            user_id=user.id
        ).annotate(
            status=F("result")
        )
        envs_srz = MyEnvSrz(envs, many=True)
        return OK(envs_srz.data)

    
    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        분반에 env 연결 API
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

        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")

        env = Env.objects.filter(
            id=data['env_id'],
            user_id=user.id,
            result='success'
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")
        
        #이미 연결된 env인지 확인
        if EnvBelongClass.objects.filter(
            class_id=data['class_id'],
            env_id__name=env.name,      #이름이 같은 env가 존재하며
            env_id__result='success'    #성공한 env인 경우
        ).exists():
            return FORBIDDEN("env is already in the class.")
        elif EnvBelongClass.objects.filter(
            class_id=data['class_id'],
            env_id__name=env.name      #이름이 같은 env가 존재
        ).exists():

            ebc = EnvBelongClass.objects.filter(
                class_id=data['class_id'],
                env_id__name=env.name
            ).first()

            Env.objects.filter(id=ebc.env_id.id).first().delete()

        ebc = EnvBelongClass(
            env_id=env,
            class_id=classes
        )
        ebc.save()

        return CREATED()

    
    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        분반에서 env 연결 해제 API
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

        ebc = EnvBelongClass.objects.filter(
            env_id=data['env_id'],
            class_id=data['class_id']
        ).first()
        if not ebc:
            return FORBIDDEN("env is not in the class.")
        
        ebc.delete()
        return NO_CONTENT
        