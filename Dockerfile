# Betty-Cropper Django server
#
FROM python:3.5
MAINTAINER Onion Tech <webtech@theonion.com>

# Grab packages and then cleanup (to minimize image size)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
        libfreetype6-dev \
        libjpeg-dev \
        libtiff5-dev \
        zlib1g-dev \
        libblas-dev \
        liblapack-dev \
        libatlas-base-dev \
        gfortran \
        vim

# Setup app directory
RUN mkdir -p /webapp
WORKDIR /webapp

COPY requirements/ /webapp/requirements/

RUN cd requirements && pip install -r common.txt \
                                   -r dev.txt 
                                   #-r imgmin.txt

# Add app as late as possibly (will always trigger cache miss and rebuild from here)
ADD . /webapp

# TODO: Necessary for uWSGI app?
RUN pip install .
#RUN pip install . \
#RUN pip install "file://$(pwd)#egg=betty-cropper[dev]"
