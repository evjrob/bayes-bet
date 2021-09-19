FROM continuumio/miniconda3

RUN apt-get update
RUN apt-get upgrade -y

RUN conda install -y python=3.8
RUN conda install -y pip setuptools wheel
RUN conda install -c conda-forge -y pymc3==3.11.4

COPY requirements.txt /workspace/bayes-bet/model/requirements.txt
RUN pip install -r /workspace/bayes-bet/model/requirements.txt

COPY pyproject.toml /workspace/bayes-bet/model/pyproject.toml
COPY setup.py /workspace/bayes-bet/model/setup.py
RUN mkdir /workspace/bayes-bet/model/bayesbet
RUN cd /workspace/bayes-bet/model && pip install -e .
COPY bayesbet /workspace/bayes-bet/model/bayesbet