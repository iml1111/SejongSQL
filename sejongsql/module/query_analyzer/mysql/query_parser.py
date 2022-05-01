"""
SQL File Parser 모듈
"""
import sqlparse
from collections import namedtuple


ParsedQuery = namedtuple(
    'Parsed',
    [
        'result',  # 진행 결과 True(성공) / False(실패)
        'origin',  # 원본 쿼리
        'tables',  # 추출된 테이블 명
        'parsed_list'  # 파싱된 쿼리 결과 (리스트)
    ]
)
Report = namedtuple('Report', ['result', 'msg'])


def parse(queries: str):
    result = []
    tables = []
    for statement in sqlparse.parse(queries):
        statement_type = statement.get_type().upper()

        if statement_type == 'CREATE':
            table_flag = False
            for token in statement.tokens:
                if (
                    str(token.ttype) == "Token.Keyword"
                    and token.value.upper() in ('TABLE', 'INDEX')
                ):
                    result.append(statement.value.strip())
                    table_flag = token.value == 'TABLE'
                    break

            # 테이블명 추출
            if table_flag:
                for token in statement.tokens:
                    if type(token).__name__ == 'Identifier':
                        if token.value not in tables:
                            tables.append(token.value)
                        else:  # Overlap detected !
                            return Report(
                                result=False,
                                msg='Duplicate table detected.'
                            )
                        break

        elif statement_type == 'INSERT':
            result.append(statement.value.strip())

    return ParsedQuery(
        result=True,
        origin=queries,
        tables=tables,
        parsed_list=result
    )


if __name__ == "__main__":
    """
    -TEST STATUS-
    a.sql (ok) -> 42 (시간 지연 체감X)
    b.sql (ok) -> 113 (시간 지연 체감X)
    book_20200331.sql (OK) -> 149개 (시간 지연 체감X)
    demo_madang.sql (OK) -> 80개 (시간 지연 체감X)
    exec_20200526.sql (OK) -> 46 개 (시간 지연 체감X)
    sample_20200331.sql (OK) -> 679개 (시간 지연 체감X)
    world.sql (OK) -> 6000개 (시간 지연 약 2~3초)
    """
    with open('exec_20200526.sql', 'r', encoding='utf-8') as f:
        queries = f.read()
        test = parse(queries)
        if test:
            # print(test.origin)
            print(test.parsed_list)
            # print(test.tables)

    import os
    from MySQLdb import connect, cursors
    db = connect(
        host="localhost",
        port=3306,
        user=os.environ['MYSQL_USER'],
        passwd=os.environ['MYSQL_PASSWORD'],
        charset='utf8mb4',
        db='test',
        cursorclass=cursors.DictCursor
    )

    # 한번에 실행
    with db.cursor() as cursor:
        cursor.execute(test.parsed_list)

    # 한줄씩 테스팅
    # for query in test.query_list:ß
    #     print(query)
    #     with db.cursor() as cursor:
    #         cursor.execute(query)
