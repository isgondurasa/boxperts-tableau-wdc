FROM ubuntu:latest
MAINTAINER sviridov.ao@yandex.ru

RUN apt-get update && apt-get install -y python-pip python-dev build-essential libssl-dev libffi-dev \
libxml2-dev libxslt1-dev libpng-dev freetype* libblas-dev gfortran

ADD requirements.txt /
RUN pip install --upgrade pip
# RUN pip install numpy

RUN pip install -r requirements.txt

ADD app.tar.bz2 /wdc
WORKDIR /wdc

ADD prod_settings.py /wdc/settings.py




