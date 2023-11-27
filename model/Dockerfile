FROM python:3.11

RUN apt-get update
RUN apt-get upgrade -y

COPY requirements.txt /workspaces/bayes-bet/model/requirements.txt
RUN pip install -r /workspaces/bayes-bet/model/requirements.txt
RUN pip install awslambdaric

ENV PYTENSOR_FLAGS='base_compiledir=/tmp/pytensor'

COPY . /workspaces/bayes-bet/model
