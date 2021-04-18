FROM python:3.8-slim-buster

WORKDIR /model

COPY Pipfile /model/Pipfile
COPY Pipfile.lock /model/Pipfile.lock
COPY pyproject.toml /model/pyproject.toml
COPY setup.py /model/setup.py
COPY bayesbet /model/bayesbet

RUN apt-get update
RUN apt-get upgrade -y

# Get G++ for Theano
RUN apt-get install -y g++ libopenblas-dev

RUN python -m pip install --upgrade pip
RUN pip install pipenv
RUN pipenv sync

CMD ["pipenv", "run", "python", "/model/bayesbet/nhl/main.py" ]
