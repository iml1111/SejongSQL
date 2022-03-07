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
	apk add --update --no-cache bash curl jpeg-dev && \
	mkdir /home/log /home/assets && \
	pip install --no-index \
	--find-links=/home/sejongsql/wheels \
	-r requirements.txt && \
	rm -rf /home/sejongsql/wheels

EXPOSE 5000

CMD ["gunicorn","-w","2", \
	"--bind","0.0.0.0:5000", \
	"--access-logfile", "/home/log/access.log", \
	"--error-logfile", "/home/log/error.log", \
	"manage:application"]