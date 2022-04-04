FROM --platform=linux/amd64 python:3.8-slim-bullseye as build-stage-1

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean

COPY requirements.txt requirements-production.txt ./
RUN pip3 install --no-cache-dir --prefix=/usr/local -r requirements.txt -r requirements-production.txt


FROM --platform=linux/amd64 python:3.8-slim-bullseye

ARG VERSION

LABEL language="python"
LABEL framework="fastapi"
LABEL usage="Full text search on GEOSS metadata"

ENV VERSION="${VERSION}"
ENV PYTHON_VERSION="3.8"
ENV PYTHONPATH="/usr/local/lib/python${PYTHON_VERSION}/site-packages"

COPY --from=build-stage-1 /usr/local /usr/local

RUN mkdir /usr/local/geoss_search/
COPY setup.py README.md requirements.txt /usr/local/geoss_search/
COPY geoss_search /usr/local/geoss_search/geoss_search

COPY docker-command.sh /usr/local/bin
RUN chmod a+x /usr/local/bin/docker-command.sh

RUN mkdir /var/local/geoss_search && \
    useradd -U --home /var/local/geoss_search fastapi && \
    chown -R fastapi: /var/local/geoss_search
WORKDIR /var/local/geoss_search
RUN mkdir ./logs && chown fastapi: ./logs
COPY --chown=fastapi logging.conf .

RUN pip3 install --upgrade pip && \
    (cd /usr/local/geoss_search && pip3 install --prefix=/usr/local . && python3 setup.py clean -a)

USER fastapi
CMD ["/usr/local/bin/docker-command.sh"]

EXPOSE 8000
EXPOSE 8443
