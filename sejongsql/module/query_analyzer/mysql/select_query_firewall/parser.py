import sqlparse

def parse_query(query: str) -> tuple:
    return sqlparse.parse(query)
