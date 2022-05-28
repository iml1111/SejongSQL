from .parser import parse_query
from .traverse import traverse

def is_safe_select_query(queries: str) -> tuple:
    '''
    /*! query */ 구문을 막기 위한 방법 중 하나로 주석이 제거된 formated_query 를 사용하는 것 이었는데, 
    오히려 주석이 제거되면서 위험한 상황이 발생할 가능성이 있어서 제거
    '''
    parsed_statements = parse_query(queries)

    if len(parsed_statements) != 1:
        '''
        Root Depth의 Statement가 1개 미만 또는 초과한 경우 차단
        주석도 1개의 Statement로 간주하므로 주의
        '''
        return (False, ['multiple statements'])

    root_statement = parsed_statements[0]

    '''
    Root Depth부터 순회하며 다수의 필터링에 어긋나는 부분이 있는 경우 차단
    '''
    detect_logs = traverse(root_statement)

    '''
    detect_logs 가 0개이면 안전, 1개 이상이면 안전하지 않음
    '''
    is_safe = len(detect_logs) == 0
    return (is_safe, detect_logs)
