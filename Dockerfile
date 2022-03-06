# syntax=docker/dockerfile:1

FROM node:14-alpine3.14

COPY requirements.txt /base/
COPY start.py /base/
WORKDIR /base/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HOSTNAME="0.0.0.0"
ENV PORT=80

RUN apk update
RUN apk add --update --no-cache python3 git py3-pip py3-psutil
RUN ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN python3 -m pip install --upgrade pip setuptools
RUN python3 -m pip install -r requirements.txt

ENTRYPOINT [ "python3", "start.py" ]

EXPOSE $PORT/tcp