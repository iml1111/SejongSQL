import os, re, shutil
from uuid import uuid4
from app_main.models import Env, EnvBelongClass, EnvBelongMe, TableBelongEnv, Queue
from module.query_analyzer.mysql.query_parser import parse
from MySQLdb import connect, cursors


def connect_to_environ():
    db = connect(
        host=os.environ['SSQL_ORIGIN_MYSQL_HOST'],
        port=int(os.environ['SSQL_ORIGIN_MYSQL_PORT']),
        user=os.environ['SSQL_ORIGIN_MYSQL_USER'],
        passwd=os.environ['SSQL_ORIGIN_MYSQL_PASSWORD'],
        charset='utf8mb4',
        db=os.environ['SSQL_ENVRION_MYSQL_DB_NAME'],
        cursorclass=cursors.DictCursor
    )

    return db


def create_env(
    user, query, env_name,
    file_name, share, type, 
    classes=None
):
    env = Env(
        user_id=user,
        name=env_name,
        file_name=f"{uuid4()}_{file_name}"
    )
    env.save()

    queue = Queue(
        user_id=user.id,
        type='create_env',
        type_id=env.id
    )
    queue.save()

    if type == 'class':
        # EnvBelongClass DB 적용
        ebc = EnvBelongClass(
            env_id=env,
            class_id=classes,
            share=share
        )
        ebc.save()
    elif type == 'mine':
        # EnvBelongMe DB 적용
        ebm = EnvBelongMe(
            env_id=env,
            user_id=user,
            share=share
        )
        ebm.save()

    # 원본파일 저장
    f = open(f"./sql_file/original/{env.file_name}", 'w', encoding='utf-8') 
    f.write(query)
    f.close()

    # sql query 파싱
    result = parse(query)
    if not result.result:
        env.result = 'parser failed'
        env.save()
        queue.status = 'complete'
        queue.save()
        return

    # SQL File 파싱 과정
    parsed_table = {nickname: f"ssql_{str(uuid4()).replace('-', '_')}" for nickname in result.tables}
    with open(f"./sql_file/parsed/{env.file_name}", 'w', encoding='utf-8') as f:
        for query in result.parsed_list:
            # CREATE / INSERT / REFERENCES 변경
            regex_dict = {
                'CREATE TABLE': "CREATE\s*TABLE\s*{}?(?=\(|\s)|CREATE\s*TABLE\s*.{}.\s*?(?=\(|\s)",
                'INSERT INTO': "INSERT\s*INTO\s*{}?(?=\(|\s)|INSERT\s*INTO\s*.{}.\s*?(?=\(|\s)",
                'REFERENCES': "REFERENCES\s*{}?(?=\(|\s)|REFERENCES\s*.{}.\s*?(?=\(|\s)"
            }
            for key, value in regex_dict.items():
                for nickname, name in parsed_table.items():
                    query = re.sub(
                        value.format(nickname, nickname),
                        f'{key} {name}',
                        string=query,
                        flags=re.IGNORECASE
                    )

            # CONSTRAINT 변경
            constraint = re.findall("CONSTRAINT\s*(`.*?`|'.*?'|\".*?\"|.*?(?=\s))", query, flags=re.IGNORECASE)
            for keyword in constraint:
                ibfk = re.findall("[a-zA-Zㄱ-ㅎ|가-힣|0-9]", keyword)
                query = query.replace(keyword, f"{''.join(ibfk)}{env.id}") #foreignkey name이 unique 해야함.
            
            f.write(query + '\n')

    # DB 삽입 과정
    with open(f"./sql_file/parsed/{env.file_name}", 'r', encoding='utf-8') as f:
        queries = f.read()

    db = connect_to_environ()
    cur = db.cursor()
    try: # 성공
        cur.execute(queries)
        env.result = 'success'
        env.save()
    except Exception as error: # 실패
        db.rollback()
        error = str(error)
        for nickname, name in parsed_table.items():
            error = error.replace(name, nickname)
        env.result = error
        env.save()
        queue.status = 'complete'
        queue.save()
        return
    finally:
        cur.close()
        db.close()

    # TableBelongEnv DB 적용
    for nickname, name in parsed_table.items():
        tbe = TableBelongEnv(
            env_id=env,
            table_name=name,
            table_nickname=nickname
        )
        tbe.save()
    
    queue.status = 'complete'
    queue.save()


def copy_env(env, user, classes=None):
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

    queue = Queue(
        user_id=user.id,
        type='copy_env',
        type_id=copy_env.id
    )
    queue.save()

    if classes:
        ebc = EnvBelongClass(
            env_id=copy_env,
            class_id=classes,
            share=1
        )
        ebc.save()
    else:
        ebm = EnvBelongMe(
            env_id=copy_env,
            user_id=user,
            share=1
        )
        ebm.save()

    tbe = TableBelongEnv.objects.filter(env_id=env.id)  #복사할 테이블
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
    
    with open(f"./sql_file/parsed/{env.file_name}", 'r', encoding='utf-8') as f:
        query = f.read()

    for original, copy in parsed_table.items(): #테이블 명 변경
        query = query.replace(original, copy)

    constraint = re.findall("CONSTRAINT\s*(`.*?`|'.*?'|\".*?\"|.*?(?=\s))", query, flags=re.IGNORECASE)
    for keyword in constraint:
        ibfk = re.findall("[a-zA-Zㄱ-ㅎ|가-힣|0-9]", keyword)
        query = query.replace(keyword, f"{''.join(ibfk)}{copy_env.id}") #foreignkey name이 unique 해야함.

    with open(f"./sql_file/parsed/{copy_env.file_name}", 'w', encoding='utf-8') as f:
        f.write(query)   #파싱한 파일 복사

    db = connect_to_environ()
    with db.cursor() as cur:
        cur.execute(query)
        env.save()
    db.commit()

    queue.status = 'complete'
    queue.save()