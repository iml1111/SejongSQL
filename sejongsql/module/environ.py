import os, string
from random import choice
from uuid import uuid4
from app_main.models import Env, EnvBelongClass, EnvBelongTable, Queue
from module.query_analyzer.mysql.query_parser import parse
from MySQLdb import connect, cursors


def get_db(
    user=os.environ['SSQL_ORIGIN_MYSQL_USER'],
    passwd=os.environ['SSQL_ORIGIN_MYSQL_PASSWORD']
):
    """
    DB Connection을 반환하는 함수
    """
    return connect(
        host=os.environ['SSQL_ORIGIN_MYSQL_HOST'],
        port=int(os.environ['SSQL_ORIGIN_MYSQL_PORT']),
        user=user,
        passwd=passwd,
        charset='utf8mb4',
        cursorclass=cursors.DictCursor
    )


def create_env(user, query, env_name, classes=None):
    uuid = str(uuid4()).replace('-','_')
    strings = string.printable[:63]
    env = Env(
        user_id=user,
        name=env_name,
        db_name=f"sejongsql_{uuid}",
        file_name=f"{uuid4()}.sql",
        account_name=f"{''.join([choice(strings) for _ in range(30)])}",
        account_pw=f"{''.join([choice(strings) for _ in range(30)])}"
    )
    env.save()

    queue = Queue(
        user_id=user.id,
        type='create_env',
        type_id=env.id
    )
    queue.save()

    if classes:
        ebc = EnvBelongClass(
            env_id=env,
            class_id=classes,
        )
        ebc.save()
    
    try:
        if not os.path.exists(os.environ['SSQL_SQL_ORIGINAL_FILE']):
            os.makedirs(os.environ['SSQL_SQL_ORIGINAL_FILE'])
        if not os.path.exists(os.environ['SSQL_SQL_PARSED_FILE']):
            os.makedirs(os.environ['SSQL_SQL_PARSED_FILE'])
    except:
        env.result = 'failed to save sql_file'
        env.save()
        queue.status = 'complete'
        queue.save()
        return

    # 원본파일 저장
    with open(
        f"{os.environ['SSQL_SQL_ORIGINAL_FILE']}/{env.file_name}",
        'w',
        encoding='utf-8'
    ) as f:
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
    with open(
        f"{os.environ['SSQL_SQL_PARSED_FILE']}/{env.file_name}",
        'w',
        encoding='utf-8'
    ) as f:
        for query in result.parsed_list:            
            f.write(query + '\n')

    db = get_db()
    cursor = db.cursor()
    try: # 성공
        cursor.execute(f"CREATE DATABASE {env.db_name};")
        db.select_db(env.db_name)
        for query in result.parsed_list:
            cursor.execute(query)
        db.commit()
        env.result = 'success'
        env.save()
    except Exception as error: # 실패
        cursor.execute(f"DROP DATABASE IF EXISTS {env.db_name};")
        env.result = str(error)
        env.save()
        queue.status = 'complete'
        queue.save()
        db.close()
        return
    
    #계정 생성
    cursor.execute(f"CREATE user '{env.account_name}'@'%' identified with 'mysql_native_password' by '{env.account_pw}';")
    cursor.execute(f"GRANT all privileges on {env.db_name}.* to '{env.account_name}'@'%' with grant option;")
    cursor.execute(f"flush privileges;")
    db.commit()
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
