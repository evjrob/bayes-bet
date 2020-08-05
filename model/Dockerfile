FROM python:slim-buster

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock
COPY nhl nhl

RUN apt-get update
RUN apt-get upgrade -y

RUN python -m pip install --upgrade pip
RUN pip install pipenv
RUN pipenv sync

CMD ["pipenv", "run", "python", "nhl/main.py" ]
