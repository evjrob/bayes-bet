FROM python:slim-buster

COPY nhl /

RUN apt-get update
RUN pip install pipenv
RUN pipenv sync

CMD ["pipenv", "run", "python", "nhl/main.py" ]
