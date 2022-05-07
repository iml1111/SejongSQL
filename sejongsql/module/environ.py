import os
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

