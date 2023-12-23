# syntax=docker/dockerfile:1

FROM python:3.9.18-slim

WORKDIR /app

RUN mkdir /app/data

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

COPY . .

CMD [ "gunicorn", "-w 4", "-b 0.0.0.0:8080", "app:app"]