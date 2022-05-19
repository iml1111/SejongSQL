FROM python:3.9-alpine as base

COPY /sejongsql/ /home/sejongsql/
WORKDIR /home/sejongsql/
COPY ./requirements.txt /home/sejongsql/requirements.txt

RUN apk update && \
	apk add --update --no-cache gcc libressl-dev \
	musl-dev libffi-dev jpeg-dev zlib-dev mariadb-connector-c-dev && \
	pip install --upgrade pip && \
	pip wheel --wheel-dir=/home/sejongsql/wheels -r requirements.txt

FROM python:3.9-alpine

# ENV VAR=value

COPY --from=base /home/sejongsql/ /home/sejongsql/

WORKDIR /home/sejongsql/

RUN apk update && \
	apk add --update --no-cache bash curl jpeg-dev mariadb-connector-c-dev && \
	mkdir /home/assets && \
	pip install --no-index \
	--find-links=/home/sejongsql/wheels \
	-r requirements.txt && \
    pip install gunicorn && \
	rm -rf /home/sejongsql/wheels

EXPOSE 5000

CMD ["gunicorn","-w","2", \
	"--bind","0.0.0.0:5000", \
	"--log-level", "debug", \
	"--access-logfile", "-", \
	"--access-logformat", "%(h)s [ACCESS] %(l)s %(u)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s'", \
	"config.wsgi:application"]