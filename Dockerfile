FROM python:3.9-slim-buster

RUN pip install pipenv

WORKDIR /

ADD Pipfile Pipfile.lock main.py /

RUN pipenv install --system --deploy

EXPOSE 8080

COPY ./app app

CMD ["python", "main.py"]