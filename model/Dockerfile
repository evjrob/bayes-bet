FROM continuumio/miniconda3

RUN apt-get update
RUN apt-get upgrade -y

# Get G++ for Theano
RUN apt-get install -y g++

RUN conda install -y python=3.8
RUN conda install -y pip setuptools wheel
run conda install -y -c conda-forge theano-pymc mkl
RUN conda install -y -c conda-forge pymc3=3.11.4

COPY requirements.txt /workspaces/bayes-bet/model/requirements.txt
RUN pip install -r /workspaces/bayes-bet/model/requirements.txt
RUN pip install awslambdaric

ENV THEANO_FLAGS='base_compiledir=/tmp/theano'

COPY . /workspaces/bayes-bet/model

