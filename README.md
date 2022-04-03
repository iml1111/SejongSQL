# SejongSQL
2022년 1학기 세종대학교 창의학기제 - SQL Online Judge

# Dependency
- Python 3.9.X

# Envirements
```shell
# Authentication 시크릿 키
SECRET_KEY=top-secret
# config 주입 정보
# development or production
DJANGO_SETTINGS_MODULE=config.settings.development

# 본 서비스 DB 정보
SSQL_ORIGIN_MYSQL_DB_NAME=sejongsql
SSQL_ORIGIN_MYSQL_USER=root
SSQL_ORIGIN_MYSQL_PASSWORD=password
SSQL_ORIGIN_MYSQL_HOST=localhost
SSQL_ORIGIN_MYSQL_PORT=3306

# mysql docker 정보
MYSQL_ROOT_PASSWORD=password
```
