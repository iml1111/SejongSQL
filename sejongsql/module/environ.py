import os
from uuid import uuid4
from app_main.models import Env, EnvBelongClass, EnvBelongTable, Queue
from module.query_analyzer.mysql.query_parser import parse
from MySQLdb import connect, cursors


def get_db():
    """
    DB Connection을 반환하는 함수
    """
    return connect(
        host=os.environ['SSQL_ORIGIN_MYSQL_HOST'],
        port=int(os.environ['SSQL_ORIGIN_MYSQL_PORT']),
        user=os.environ['SSQL_ORIGIN_MYSQL_USER'],
        passwd=os.environ['SSQL_ORIGIN_MYSQL_PASSWORD'],
        charset='utf8mb4',
        cursorclass=cursors.DictCursor
    )


def create_env(
    user, query, 
    env_name, file_name,
    classes=None
):
    env = Env(
        user_id=user,
        name=env_name,
        db_name=f'{env_name}_{user.id}',
        file_name=f"{uuid4()}_{file_name}"
    )
    env.save()

    queue = Queue(
        user_id=user.id,
        type='create_env',
        type_id=env.id
    )
    queue.save()

    ebc = EnvBelongClass(
        env_id=env,
        class_id=classes,
    )
    ebc.save()

    # 원본파일 저장
    with open(f"./sql_file/original/{env.file_name}", 'w', encoding='utf-8') as f:
        f.write(query)

    # sql query 파싱
    result = parse(query)
    if not result.result:
        env.result = 'parser failed'
        env.save()
        queue.status = 'complete'
        queue.save()
        return

    # SQL File 파싱 과정
    with open(f"./sql_file/parsed/{env.file_name}", 'w', encoding='utf-8') as f:
        for query in result.parsed_list:            
            f.write(query + '\n')

    db = get_db()
    cursor = db.cursor()
    try: # 성공
        cursor.execute(f"CREATE DATABASE {env.db_name};")
        db.select_db(env.db_name)
        for query in result.parsed_list:
            cursor.execute(query)
        env.result = 'success'
        env.save()
    except Exception as error: # 실패
        cursor.execute(f"DROP DATABASE IF EXISTS {env.db_name};")
        env.result = str(error)
        env.save()
        queue.status = 'complete'
        queue.save()
        return
    finally:
        db.close()

    # EnvBelongTable DB 적용
    for name in result.tables:
        tbe = EnvBelongTable(
            env_id=env,
            table_name=name
        )
        tbe.save()
    
    queue.status = 'complete'
    queue.save()
