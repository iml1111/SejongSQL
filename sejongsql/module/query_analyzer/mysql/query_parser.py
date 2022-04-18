import sqlparse
from uuid import uuid4
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedQuery:
    origin: str  # 원본 쿼리
    parsed: str  # 파싱된 쿼리
    tables: dict  # 추출된 테이블 명
    query_list: list  # 파싱된 쿼리 리스트 (단일 쿼리들의 리스트)


def parse(queries: str):
    result = []
    tables = {}
    for statement in sqlparse.parse(queries):
        statement_type = statement.get_type().upper()

        if statement_type == 'CREATE':
            table_flag = False
            for token in statement.tokens:
                if (
                    str(token.ttype) == "Token.Keyword"
                    and token.value.upper() in {'TABLE', 'INDEX'}
                ):
                    result.append(statement.value.strip())
                    if token.value == 'TABLE':
                        table_flag = True
                    break

            # 테이블명 추출
            if table_flag:
                for token in statement.tokens:
                    if type(token).__name__ == 'Identifier':
                        if token.value not in tables:
                            uid = str(uuid4())
                            tables[token.value] = uid
                            tables[uid] = token.value
                        else:  # Overlap detected !
                            return None
                        break

        elif statement_type == 'INSERT':
            result.append(statement.value.strip())

    return ParsedQuery(
        origin=queries,
        parsed='\n'.join(result),
        tables=tables,
        query_list=result
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
            print(test.parsed)
            # print(test.query_list)
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
        cursor.execute(test.parsed)

    # 한줄씩 테스팅
    # for query in test.query_list:
    #     print(query)
    #     with db.cursor() as cursor:
    #         cursor.execute(query)
