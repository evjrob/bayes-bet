FROM python:3.8

RUN apt-get update
RUN apt-get upgrade -y

# Get G++ for Theano
RUN apt-get install -y g++

COPY requirements.txt /workspaces/bayes-bet/model/requirements.txt
RUN pip install -r /workspaces/bayes-bet/model/requirements.txt

COPY pyproject.toml /workspaces/bayes-bet/model/pyproject.toml
COPY setup.py /workspaces/bayes-bet/model/setup.py
RUN mkdir /workspaces/bayes-bet/model/bayesbet
RUN cd /workspaces/bayes-bet/model && pip install -e .
COPY bayesbet /workspaces/bayes-bet/model/bayesbet
