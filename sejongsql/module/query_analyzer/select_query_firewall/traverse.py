'''traverse module'''
from sqlparse.tokens import Token

def is_unsafe_identifier(identifier: str):
    return identifier.upper() in [
        'INFORMATION_SCHEMA',
        'MYSQL',  # mysql.user -> hashed passwd crack
        'PERFORMANCE_SCHEMA',
        'SYS',
        'OUTFILE',   # secure_file_priv
        'LOAD_FILE'  # secure_file_priv
    ]

def traverse(
    statement,
    prev_token = None,  # FIXME: 1.0.0 개발까지 사용하지 않으면 삭제
    detect_logs = None
) -> list[str]:
    if detect_logs is None:
        detect_logs = []

    tokens = statement.tokens
    for token in tokens:
        # 토큰 정보 확인 용도
        # print(f'{token.is_group}\t{token.is_keyword}\t{token.ttype}\t{token.value}\t{prev_token}')

        # 공백인 경우 아래 절차 생략, prev_token 갱신하지 않음
        if token.ttype is Token.Text.Whitespace:
            continue

        # 주석인 경우
        if token.ttype is Token.Comment.Multiline:
            # /*! 로 시작하는 경우 차단
            if token.value.startswith('/*!'):
                detect_logs.append(token.value)

            # /*+ 로 시작하는 경우 차단
            if token.value.startswith('/*+'):
                detect_logs.append(token.value)

            # 주석이면 아래 절차 생략, prev_token 갱신하지 않음
            continue

        # (something) 형태인 경우 재귀 분석
        if token.is_group:
            traverse(token, prev_token, detect_logs)
        # 이 외의 모든 경우
        else:
            if token.is_keyword:
                # CTE(WITH) 차단
                if token.ttype is Token.Keyword.CTE:
                    detect_logs.append(token.value)
                # DDL(DROP, CREATE, ALTER) 차단
                elif token.ttype is Token.Keyword.DDL:
                    detect_logs.append(token.value)
                # SELECT 제외한 DML 절 차단
                elif token.ttype is Token.Keyword.DML \
                    and token.value.upper() != 'SELECT':
                    detect_logs.append(token.value)

            # 식별자라고 볼 수 있는 것은 Token.name 또는 Token.Keyword
            if token.ttype is Token.Name or token.ttype is Token.Keyword:
                if is_unsafe_identifier(token.value):
                    detect_logs.append(token.value)

            # 연산자인 경우
            elif token.ttype is Token.Operator:
                # 로컬 변수 접근 연산자 차단
                if token.value == '@':
                    detect_logs.append(token.value)

                # 시스템 변수 접근 연산자 차단
                if token.value == '@@':
                    detect_logs.append(token.value)

            # grouping 아닌 경우에만 prev_token 갱신
            prev_token = token

    return detect_logs
