from collections import namedtuple


WarningReport = namedtuple(
    'WarningReport',
    ['code', 'msg']
)


FULL_TABLE_SCAN = WarningReport(
    code='full_table_scan',
    msg='풀 테이블 스캔이 감지되었습니다.'
)


NO_JOIN = WarningReport(
    code='no_join',
    msg='해당 쿼리에는 Join이 감지되지 않았습니다.'
)


FILE_SORT = WarningReport(
    code='file_sort',
    msg=(
        '메모리 혹은 디스크상의 정렬이 수행되었습니다. '
        '결과 데이터가 많은 경우 성능에 직접적인 영향을 줄 수 있습니다.'
    )
)


IMPOSSIBLE_CONDITION = WarningReport(
    code='impossible_condition',
    msg=(
        '테이블 구조상 WHERE/HAVING 조건이 항상 false가 될 수 밖에 '
        '없는 경우에 이 경고가 표시됩니다.'
    )
)


UNCACHEABLE = WarningReport(
    code='uncacheable',
    msg=(
        '외부에 공급되는 모든 값에 대하여, 캐싱이 불가능해'
        '해당 UNION/서브쿼리를 매번 재실행합니다.'
    )
)
