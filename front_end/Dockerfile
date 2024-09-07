FROM python:3.11

WORKDIR /app

RUN apt-get update
RUN apt-get upgrade -y

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY app /app
