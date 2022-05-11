from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Path, Form, File
from module.decorator import login_required, get_user
from module.environ import connect_to_environ, create_env
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
        
        envs = EnvBelongClass.objects.filter(   #성공한 env만 반환
            class_id=data['class_id'],
            env_id__result='success'
        ).annotate(
            envid=F('env_id__id'),
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

        q = get_async_queue(worker_num=3, qsize=100)
        q.add(freeze(create_env)(
            user=user,
            classes=classes,
            query=query,
            env_name=data['name'],
            file_name=data['file'].name,
            share=data['share']
        ))

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

        db = connect_to_environ()

        tbe = TableBelongEnv.objects.filter(env_id=env.id)
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
        내 소속 Env 반환 API
        """

        user = get_user(request)
        envs = Env.objects.filter(  #성공, 실패 상관없이 반환
            user_id=user.id,
        ).annotate(
            envid=F('id'),
            owner=F('user_id')
        )
        envs_srz = EnvSrz(envs, many=True)
        return OK(envs_srz.data)


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        Env 복사 API
        SA, 교수, 조교 호출 가능 
        """
        #학생도 가능하게 수정
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
            result='success'
        ).filter(
            envbelongclass__class_id=data['class_id'],   #해당 분반에 있는 env만 복사 가능
            envbelongclass__share=1    #공유허가된 env만 복사 가능
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")
        
        file_name = str(env.file_name)
        file_name = file_name.replace(file_name[:36], str(uuid4()))
        #uuid는 36자리
    
        copy_env = Env(
            user_id=user,
            name=env.name,
            file_name=file_name,
            result = 'success'
        )
        copy_env.save()

        tbe = TableBelongEnv.objects.filter(env_id=data['env_id'])  #복사할 테이블
        parsed_table = {}
        for table in tbe:
            uuid = str(uuid4())
            uuid = uuid.replace('-', '_')
            copy_tbe = TableBelongEnv(
                env_id=copy_env,
                table_name=f'ssql_{uuid}',
                table_nickname=table.table_nickname
            )
            copy_tbe.save()
            parsed_table[table.table_name] = copy_tbe.table_name
        
        origin_source = f"./sql_file/original/{env.file_name}"
        origin_destination = f"./sql_file/original/{copy_env.file_name}"
        shutil.copyfile(origin_source, origin_destination)    #원본파일 복사
        
        f = open(f"./sql_file/parsed/{env.file_name}", 'r', encoding='utf-8')
        query = f.read()
        f.close()

        for original, copy in parsed_table.items(): #테이블 명 변경
            query = query.replace(original, copy)

        re_con = re.compile("CONSTRAINT\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))", re.I)
        constraint = re_con.findall(query)

        for keyword in constraint:
            re_ibfk = re.compile("[a-zA-Zㄱ-ㅎ|가-힣|0-9]", re.I)
            ibfk = re_ibfk.findall(keyword)
            query = query.replace(keyword, f"{''.join(ibfk)}{copy_env.id}")

        f = open(f"./sql_file/parsed/{copy_env.file_name}", 'w', encoding='utf-8')
        f.write(query)
        f.close()   #파싱한 파일 복사
  
        db = connect_to_environ()
        with db.cursor() as cur:
            cur.execute(query)
            env.save()
        db.commit()
        
        return CREATED()