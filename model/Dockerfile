FROM python:3.11

RUN apt-get update
RUN apt-get upgrade -y

COPY requirements.txt /workspaces/bayes-bet/model/requirements.txt
RUN pip install -r /workspaces/bayes-bet/model/requirements.txt
RUN pip install awslambdaric

ENV PYTENSOR_FLAGS='base_compiledir=/tmp/pytensor'

COPY . /workspaces/bayes-bet/model

# Add Lambda Runtime Interface Emulator for local runs
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
RUN chmod +x /usr/bin/aws-lambda-rie
