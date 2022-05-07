from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Path, Form, File
from module.decorator import login_required, get_user
from module.environ import connect_to_environ
from module.query_analyzer.mysql.query_parser import parse
from django_jwt_extended import jwt_required
from app_main.models import Class, Env, EnvBelongClass, TableBelongEnv
from app_main.serializer import EnvInEbcSrz, EnvSrz
from django.db.models import F
from uuid import uuid4
import shutil
import re

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

        result = parse(query)   #sql query 파싱
        if not result.result:
            return FORBIDDEN("Incorrect sql file.")
        
        env = Env(
            user_id=user,
            name=data['name'],
            file_name=f"{uuid4()}_{data['file'].name}"
        )
        env.save()

        ebc = EnvBelongClass(
            env_id=env,
            class_id=classes,
            share=data['share'] or 1
        )
        ebc.save()

        parsed_table = {}
        for nickname in result.tables:
            uuid = str(uuid4())
            uuid = uuid.replace('-', '_')   #table_name으로 사용할 uuid 파싱
            tbe = TableBelongEnv(
                env_id=env,
                table_name=f'ssql_{uuid}',
                table_nickname=nickname
            )
            tbe.save()
            parsed_table[nickname]= tbe.table_name

        re_create = re.compile("CREATE\s*TABLE\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))", re.I)
        re_insert = re.compile("INSERT\s*INTO\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))", re.I)
        re_con = re.compile("CONSTRAINT\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))", re.I)
        re_refer = re.compile("REFERENCES\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))", re.I)
        
        #정민이한테 parser 통과 못하는거 뭐뭐 있는지 물어보기
        #ex) create table 소문자는 통과 안됨.

        f = open(f"./sql_file/success/{env.file_name}", 'w', encoding='utf-8')
        try:
            for query in result.parsed_list:
                create_table = re_create.findall(query)
                insert_into = re_insert.findall(query)
                constraint = re_con.findall(query)
                reference = re_refer.findall(query)

                for keyword in create_table:
                    query = query.replace(keyword, parsed_table[keyword])
                
                for keyword in insert_into:
                    query = query.replace(keyword, parsed_table[keyword])

                for keyword in constraint:
                    re_ibfk = re.compile("[a-zA-Zㄱ-ㅎ|가-힣|0-9]", re.I)
                    ibfk = re_ibfk.findall(keyword)
                    query = query.replace(keyword, f"{''.join(ibfk)}{env.id}") #foreignkey name이 unique 해야함.

                for keyword in reference:
                    query = query.replace(keyword, parsed_table[keyword])
                
                f.write(query + '\n')
            f.close()
        except:
            f.close()
            env.status = '실패'
            env.save()
            shutil.move(
                f"./sql_file/success/{env.file_name}",
                f"./sql_file/fail/{env.file_name}"
            )   #실패한 sql 파일집으로 이동
            return FORBIDDEN("Incorrect sql file.")

        #env queue에서 성공, 진행중, 실패를 알려줄건데, 만약 실패하면 실패한 env는 그대로 살아있는건가? 어디서 실패했는지 찾으려면 살아있어야할듯
                
        f = open(f"./sql_file/success/{env.file_name}", 'r', encoding='utf-8')

        db = connect_to_environ()
        cur = db.cursor()

        queries = f.read()
        try:
            cur.execute(queries)
            env.status = '성공'
            env.save()
        except:
            #env.delete()
            env.status = '실패'
            env.save()
            cur.close()
            db.close()
            f.close()
            shutil.move(
                f"./sql_file/success/{env.file_name}",
                f"./sql_file/fail/{env.file_name}"
            )
            return FORBIDDEN("Incorrect sql file.")
        cur.close()
        db.close()
        f.close()

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

        tbe = TableBelongEnv.objects.filter(id=env.id)
        with db.cursor() as cursor:
            for table in tbe:
                cursor.execute(f"delete from {table.table_name}")
            db.commit()

        env.delete()
        
        return NO_CONTENT
#Env 삭제하면 Environ DB에 있는 실제 테이블들도 삭제해주지? yes

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

        env = Env.objects.filter(id=data['env_id']).prefetch_related(   #복사할 env
            'envbelongclass_set'
        ).filter(
            share=1     #공유허가된 env만 복사 가능
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")

        file_name = str(env.file_name)
        file_name = file_name.replace(env.user_id, user.id)
        copy_env = Env(
            user_id=user,
            name=env.name,
            file_name=file_name,
            #status
        )
        copy_env.save()

        tbe = TableBelongEnv.objects.filter(id=data['env_id'])  #복사할 테이블
        parsed_table = {}
        for table in tbe:
            uuid = str(uuid4())
            uuid = uuid.replace('-', '_')
            copy_tbe = TableBelongEnv(
                env_id=copy_env,
                table_name=f'code_{uuid}',
                table_nickname=table.table_nickname
            )
            copy_tbe.save()
            parsed_table[table.table_nickname] = copy_tbe.table_name
        
        source = f"./sql_file/success/{env.file_name}"
        destination = f"./sql_file/success/{copy_env.file_name}"
        shutil.copyfile(source, destination)    #파일 복사

        db = connect_to_environ()

        copy_tbe = TableBelongEnv.objects.filter(id=copy_env.id)    #복사한 테이블
        with db.cursor() as cursor:
            for table, copy_table in zip(tbe, copy_tbe):
                cursor.execute(
                    f"create table '{copy_table.table_name}' select * from '{table.table_name}'"
                )   #테이블 구조와 데이터 복사
            db.commit()
        
        return CREATED()
#Env 복사하면 실제 Environ DB에도 그 테이블들이 새로 생기는거지??
#Environ DB에서 해당 테이블 가져와서 새로운 이름으로 테이블 생성하고, 그걸 넣어줘야할듯
