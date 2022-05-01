import os
from MySQLdb import connect, cursors
from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Path, Form, File
from module.decorator import login_required, get_user
from module.query_analyzer.mysql.query_parser import parse
from django_jwt_extended import jwt_required
from app_main.models import Class, Env, EnvBelongClass, TableBelongEnv
from app_main.serializer import EnvInEbcSrz, EnvSrz
from django.db.models import F
from uuid import uuid4


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
        #utf-8로 디코딩 했을 때 터지거나, 좆같은 값이 나오면 내가 쳐내야함.
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

        try:
            query = data['file'].read().decode('utf-8')
        except:
            return FORBIDDEN("Incorrect sql file.")
        
        result = parse(query)
        
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
            share=data['share'] or 1
        )
        ebc.save()

        for nickname in result.tables:
            tbe = TableBelongEnv(
                env_id=env,
                table_name=uuid4(),
                table_nickname=nickname
            )
            tbe.save()
        
        db = connect(
            host=os.environ['SSQL_ORIGIN_MYSQL_HOST'],
            port=int(os.environ['SSQL_ORIGIN_MYSQL_PORT']),
            user=os.environ['SSQL_ORIGIN_MYSQL_USER'],
            passwd=os.environ['SSQL_ORIGIN_MYSQL_PASSWORD'],
            charset='utf8mb4',
            db=os.environ['SSQL_ENVRION_MYSQL_DB_NAME'],
            cursorclass=cursors.DictCursor
        )   #아마 모듈화 해야하지 않을까..

        tbe = TableBelongEnv.objects.filter(id=env.id)

        for query in result.parsed_query:
            for table in result.tables:
                if table in query:
                    query = query.replace(table, )
                    break

            with db.cursor() as cursor:
                cursor.execute(query)        

#        with db.cursor() as cursor:
#            cursor.execute(query)

        return CREATED()
#Env 생성하면서 Environ DB에 실제 테이블 넣어주기


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

        db = connect(
            host=os.environ['SSQL_ORIGIN_MYSQL_HOST'],
            port=os.environ['SSQL_ORIGIN_MYSQL_PORT'],
            user=os.environ['SSQL_ORIGIN_MYSQL_USER'],
            passwd=os.environ['SSQL_ORIGIN_MYSQL_PASSWORD'],
            charset='utf8mb4',
            db=os.environ['SSQL_ENVRION_MYSQL_DB_NAME=environ'],
            cursorclass=cursors.DictCursor
        )   #아마 모듈화 해야하지 않을까..

        tbe = TableBelongEnv.objects.filter(id=env.id)
        with db.cursor() as cursor:
            for table in tbe:
                cursor.execute(f"delete from '{table.table_name}'")
            cursor.commit()

        env.delete()
        return NO_CONTENT
#Env 삭제하면 Environ DB에 있는 실제 테이블들도 삭제해주지?

class MyEnvView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        내 소속 Env 반환 API
        """

        user = get_user(request)
        envs = Env.objects.filter(id=user.id)
        envs_srz = EnvSrz(envs, many=True)
        return OK(envs_srz.data)


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

        env = Env.objects.filter(id=data['env_id']).prefetch_related(
            'envbelongclass_set'
        ).filter(
            share=1     #공유허가된 env만 복사 가능
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")

        copy_env = Env(
            user_id=user,
            name=env.name,
            file_name=env.file_name,
            #status
        )
        copy_env.save()

        tbe = TableBelongEnv.objects.filter(id=data['env_id'])  #복사할 테이블
        for table in tbe:
            copy_tbe = TableBelongEnv(
                env_id=copy_env,
                table_name=uuid4(),
                table_nickname=table.table_nickname
            )
            copy_tbe.save() #혹시 save를 여러 번 하면 성능저하가 일어날까용?

        db = connect(
            host=os.environ['SSQL_ORIGIN_MYSQL_HOST'],
            port=os.environ['SSQL_ORIGIN_MYSQL_PORT'],
            user=os.environ['SSQL_ORIGIN_MYSQL_USER'],
            passwd=os.environ['SSQL_ORIGIN_MYSQL_PASSWORD'],
            charset='utf8mb4',
            db=os.environ['SSQL_ENVRION_MYSQL_DB_NAME'],
            cursorclass=cursors.DictCursor
        )   #아마 모듈화 해야하지 않을까..

        copy_tbe = TableBelongEnv.objects.filter(id=copy_env.id)    #복사한 테이블
        with db.cursor() as cursor:
            for table, copy_table in zip(tbe, copy_tbe):
                cursor.execute(
                    f"create table '{copy_table.table_name}' select * from '{table.table_name}'"
                )   #테이블 구조와 데이터 복사
            cursor.commit()
        
        return CREATED()
#Env 복사하면 실제 Environ DB에도 그 테이블들이 새로 생기는거지??
#Environ DB에서 해당 테이블 가져와서 새로운 이름으로 테이블 생성하고, 그걸 넣어줘야할듯
