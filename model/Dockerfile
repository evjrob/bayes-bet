FROM python:3.8-slim-buster

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
COPY bayesbet bayesbet

RUN apt-get update
RUN apt-get upgrade -y

# Get G++ for Theano
RUN apt-get install -y g++ libopenblas-dev

RUN python -m pip install --upgrade pip
RUN pip install pipenv
RUN pipenv sync

CMD ["pipenv", "run", "python", "bayesbet/nhl/main.py" ]
