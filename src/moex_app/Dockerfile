########
# Dockerfile to build MOEX App container images
########

FROM python:3.10.12-slim

WORKDIR /app

# Установка необходимых зависимостей для работы psycopg, 
# иначе компицяция падала с ошибкой:
# ImportError: no pq wrapper available.
# Attempts made:
# - couldn't import psycopg 'c' implementation: No module named 'psycopg_c'
RUN apt-get update && \
    apt-get install -y libpq-dev

COPY . .

RUN pip3 install --upgrade pip
COPY requirements/moex_app.txt ./requirements.txt
RUN pip3 install -r requirements.txt
