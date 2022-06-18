import os, string
from time import time
from random import choice
from uuid import uuid4
from collections import defaultdict
from app_main.models import (
    Env, EnvBelongClass, EnvBelongTable,
    Queue, User, Class,
    Warning, WarningBelongUp, UserSolveProblem
)
from app_main.serializer import WarningSrz
from module.query_analyzer.mysql.query_validator import SELECTQueryValidator
from module.query_analyzer.mysql.query_explainer import QueryExplainer
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
    user = User.objects.get(id=user)
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
        classes = Class.objects.get(id=classes)
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

    tables = []
    while result.tables:
        target = result.tables.pop(0)
        flag = False
        for table in result.tables:
            if target in table:
                result.tables.append(target)
                flag = True
                break
        if flag:
            continue
        tables.append(target)

    parsed_list = []
    # SQL File 파싱 과정
    with open(
        f"{os.environ['SSQL_SQL_PARSED_FILE']}/{env.file_name}",
        'w',
        encoding='utf-8'
    ) as f:
        for query in result.parsed_list:
            for table in tables:
                query = query.replace(table, table.lower())            
            parsed_list.append(query)            
            f.write(query + '\n')

    db = get_db()
    cursor = db.cursor()
    try: # 성공
        cursor.execute(f"CREATE DATABASE {env.db_name};")
        db.select_db(env.db_name)
        for query in parsed_list:
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
            table_name=name.lower()
        )
        tbe.save()
    
    queue.status = 'complete'
    queue.save()


def run_problem(env, query):
    db = get_db(
        user=env.account_name,
        passwd=env.account_pw
    )
    cursor = db.cursor()
    db.select_db(env.db_name)

    validator = SELECTQueryValidator(
        uri="mysql://" + str(env.account_name) + ":" +
            str(env.account_pw) + "@" +
            os.environ['SSQL_ORIGIN_MYSQL_HOST'] + ":" +
            os.environ['SSQL_ORIGIN_MYSQL_PORT'] + "/" +
            str(env.db_name)
    )
    validator_result = validator.check_query(query=query)

    status = True
    if validator_result.result:
        cursor.execute(query)
        query_result = cursor.fetchall()
    else:
        status = False
        query_result = validator_result.msg
        query_result = query_result.replace(f"{env.db_name}.", "")
        query_result = query_result.replace(env.db_name, "")
        index_1 = query_result.find('"')
        index_2 = query_result.find("'")
        if index_1 != -1: # 쌍따옴표로 감싸진 mysql error문
            query_result = query_result[index_1+1: -2]
        elif index_2 != -1: #따옴표로 감싸진 mysql error문
            query_result = query_result[index_2+1: -2]
        
    return status, query_result


def submit_problem(user, problem, env, query, warnings):
    db = get_db(
        user=env.account_name,
        passwd=env.account_pw
    )
    cursor = db.cursor()
    db.select_db(env.db_name)

    explain = QueryExplainer(
        uri="mysql://" + str(env.account_name) + ":" +
            str(env.account_pw) + "@" +
            os.environ['SSQL_ORIGIN_MYSQL_HOST'] + ":" +
            os.environ['SSQL_ORIGIN_MYSQL_PORT'] + "/" +
            str(env.db_name)
    )
    res = explain.explain_query(query)

    if res.report_type == 'validation_report':  #올바르지 않은 쿼리
        status = False
        accuracy = False
        warning_result = [] #실행이 불가능한 쿼리는 warning도 걸리지 않음

        usp = UserSolveProblem(
            p_id=problem,
            user_id=user,
            query=query,
            accuracy=accuracy,
            submit=True,
        )
        usp.save()
    else:
        answer = problem.answer.lower().replace('\n', '').replace(' ','')
        tic = time()
        cursor.execute(query)
        toc = time()
        query_result = cursor.fetchall()

        cursor.execute(problem.answer.lower())
        answer_result = cursor.fetchall()

        if 'orderby' in answer: #정답에서 order by를 요구할 때
            accuracy = True if query_result == answer_result else False
        else:
            #해시화해서 비교
            hash_dict = defaultdict(str)
            p_answer = set()
            for id, result in enumerate(answer_result):
                hash_dict[str(result)] = f"HASH{id}"
                p_answer.add(f"HASH{id}")

            u_answer = set()
            for result in query_result:
                u_answer.add(hash_dict[str(result)])
                
            accuracy = True if u_answer == p_answer else False  
        
        checked_warnings = [warning.code for warning in res.warnings]

        if (toc-tic) > problem.timelimit:   #시간초과
            checked_warnings.append('time_limit')
        
        user_warnings = Warning.objects.filter(
            id__in=warnings,    #문제에 걸린 warning 중에서
            name__in=checked_warnings   #user가 걸린 warning 반환
        )

        usp = UserSolveProblem(
            p_id=problem,
            user_id=user,
            query=query,
            accuracy=accuracy,
            submit=True,
        )
        usp.save()

        for warning in user_warnings:
            wbp = WarningBelongUp(
                up_id=usp,
                warning_id=warning
            )
            wbp.save()

        status = True
        warning_result = WarningSrz(user_warnings, many=True).data
    return status, accuracy, warning_result


def get_table(env):
    desc_table = []
    
    db = get_db(
        user=env.account_name,
        passwd=env.account_pw
    )

    cursor = db.cursor()
    db.select_db(env.db_name)

    env_table = EnvBelongTable.objects.filter(
        env_id = env.id
    ).values_list('table_name', flat=True)

    for table in env_table:
        cursor.execute(f'desc {table};')
        desc_result = cursor.fetchall()
        
        desc_dict = {}
        desc_temp = []
        for result in desc_result:
            query_dict = {}
            query_dict['Field'] = result['Field']
            query_dict['Type'] = result['Type']
            query_dict['Key'] = result['Key']
            query_dict['Null'] = result['Null']
            desc_temp.append(query_dict)
            
        desc_dict['table_name'] = table
        desc_dict['value'] = desc_temp
        desc_table.append(desc_dict)
    
    return desc_table