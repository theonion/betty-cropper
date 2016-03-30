# Betty Cropper Django server with support for
#   - uWSGI
#   - Postgres
#   - Memcached
#   - AWS S3 storage
#   - Sentry
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
        libmemcached-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Fixed settings we always want (and simplifies uWSGI invocation)
ENV UWSGI_MODULE=betty.wsgi:application \
    UWSGI_MASTER=1

# Extra packages for Onion deployment
RUN pip install "boto==2.39.0" \
                "django-storages==1.4" \
                "psycopg2==2.6.1" \
                "pylibmc==1.5.1" \
                "raven==4.2.1" \
                "uwsgi>=2.0.11.1,<=2.1"

# Setup app directory
RUN mkdir -p /webapp
WORKDIR /webapp

COPY requirements/ /webapp/requirements/

RUN cd requirements && pip install -r common.txt \
                                   -r dev.txt \
                                   -r imgmin.txt

# Add app as late as possibly (will always trigger cache miss and rebuild from here)
ADD . /webapp

RUN pip install .
