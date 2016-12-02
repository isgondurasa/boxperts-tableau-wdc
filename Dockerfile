FROM ubuntu:latest
MAINTAINER sviridov.ao@yandex.ru

RUN apt-get update && apt-get install -y python-pip python-dev build-essential libssl-dev libffi-dev \
libxml2-dev libxslt1-dev

COPY . /wdc
WORKDIR /wdc

RUN pip install -r requirements.txt

