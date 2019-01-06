FROM continuumio/miniconda3

COPY bayes_bet_update.py .
COPY bayes_bet_aws.yml .

RUN apt-get update
RUN apt-get -y install build-essential
RUN conda env create -f bayes_bet_aws.yml
RUN echo "source activate bayes_bet_aws" > ~/.bashrc
ENV PATH /opt/conda/envs/bayes_bet_aws/bin:$PATH

CMD [ "python", "bayes_bet_update.py" ]
