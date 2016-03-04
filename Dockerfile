FROM python:3.5
MAINTAINER Onion Tech <webtech@theonion.com>

# Grab packages and then cleanup (to minimize image size)
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
        libmemcached-dev \
        libpq-dev \
        libfreetype6-dev \
        libjpeg-dev \
        libtiff5-dev \
        zlib1g-dev \
        libblas-dev \
        liblapack-dev \
        libatlas-base-dev \
        gfortran \
        vim \
    && rm -rf /var/lib/apt/lists/*

# Deployment requirementsl. Docker-py used for assigned port detection workaround.
RUN pip install "uwsgi>=2.0.11.1,<=2.1" \
                "docker-py==1.4.0"

# TODO: Need to work these out, as they are currently installed on deployment
RUN pip install psycopg2 \
                pylibmc \
                "raven==4.2.1"

# Fixed settings we always want (and simplifies uWSGI invocation)
ENV UWSGI_MODULE=combine.wsgi:application \
    UWSGI_MASTER=1

# Setup app directory
#RUN mkdir -p /webapp
WORKDIR /webapp

# Add app as late as possibly (will always trigger cache miss and rebuild from here)
ADD . /webapp

# TODO: Is this the best way to install? Wnat to be able to run tests too.
# This way doesn't allow for caching, better to install some requirements files before ADD-ing base dir
RUN pip install -e . \
    && pip install "file://$(pwd)#egg=betty-cropper[dev]"
