import os, re
from uuid import uuid4
from app_main.models import Env, EnvBelongClass, TableBelongEnv, Queue
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


def create_env(user, classes, query, env_name, file_name, share):
    file_uuid = uuid4()
    env = Env(
        user_id=user,
        name=env_name,
        file_name=f"{file_uuid}_{file_name}"
    )
    env.save()

    queue = Queue(
        user_id=user.id,
        type='create_env',
        type_id=env.id
    )
    queue.save()

    f = open(f"./sql_file/original/{env.file_name}", 'w', encoding='utf-8') 
    f.write(query)  #원본파일 저장
    f.close()

    result = parse(query)   #sql query 파싱
    if not result.result:
        env.result = 'parser failed'
        env.save()
        queue.status = 'complete'
        queue.save()
        return
    print(result.tables)
    parsed_table = {}
    for nickname in result.tables:
        uuid = str(uuid4())
        uuid = uuid.replace('-', '_')   #table_name으로 사용할 uuid 파싱
        parsed_table[nickname]= f'ssql_{uuid}'


    f = open(f"./sql_file/parsed/{env.file_name}", 'w', encoding='utf-8')
    for query in result.parsed_list:
        for nickname, name in parsed_table.items():
            query = query.replace(nickname, name)
        f.write(query + '\n')
    f.close()
    """
    re_create = re.compile(
        "CREATE\s*TABLE\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))",
        re.I
    )
    re_insert = re.compile(
        "INSERT\s*INTO\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))",
        re.I
    )
    re_con = re.compile(
        "CONSTRAINT\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))",
        re.I
    )
    re_refer = re.compile(
        "REFERENCES\s*(\`.*?\`|\'.*?\'|\".*?\"|.*?(?=\(|\s))",
        re.I
    )

    f = open(f"./sql_file/parsed/{env.file_name}", 'w', encoding='utf-8')
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
    except Exception as e:
        e = str(e)
        for nickname, name in parsed_table.items():
            e = e.replace(name, nickname)
        f.close()
        env.result = e
        env.save()
        queue.status = 'complete'
        queue.save()
        return
    
    f = open(f"./sql_file/parsed/{env.file_name}", 'r', encoding='utf-8')
    queries = f.read()
    f.close()

    db = connect_to_environ()
    try:
        with db.cursor() as cur:
            cur.execute(queries)
        env.result = 'success'
        env.save()
    except Exception as e:
        e = str(e)
        for nickname, name in parsed_table.items():
            e = e.replace(name, nickname)
        env.result = e
        env.save()
        queue.status = 'complete'
        queue.save()
        return

    ebc = EnvBelongClass(
        env_id=env,
        class_id=classes,
        share=share or 1
    )
    ebc.save()

    for nickname, name in parsed_table.items():
        tbe = TableBelongEnv(
            env_id=env,
            table_name=name,
            table_nickname=nickname
        )
        tbe.save()
    """
    queue.status = 'complete'
    queue.save()