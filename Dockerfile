FROM python:3.8-slim-bullseye as build-stage-1

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean

COPY requirements.txt requirements-production.txt ./
RUN pip3 --no-cache-dir install --upgrade pip wheel && \
    pip3 --no-cache-dir install --prefix=/usr/local -r requirements.txt

# BASE Image
FROM python:3.8-slim-bullseye as base

ARG VERSION

ENV VERSION="${VERSION}"
ENV PYTHON_VERSION="3.8"
ENV PYTHONPATH="/usr/local/lib/python${PYTHON_VERSION}/site-packages"

COPY --from=build-stage-1 /usr/local /usr/local

# PRODUCTION Image
FROM base as production

LABEL language="python"
LABEL framework="fastapi"
LABEL usage="Full text search on GEOSS metadata"

RUN mkdir /usr/local/geoss_search/
COPY setup.py README.md requirements-production.txt elastic_schema.yml /usr/local/geoss_search/
COPY geoss_search /usr/local/geoss_search/geoss_search

COPY docker-command.sh /usr/local/bin
RUN chmod a+x /usr/local/bin/docker-command.sh

RUN mkdir /var/local/geoss_search
WORKDIR /var/local/geoss_search
RUN mkdir ./logs
COPY logging.conf .

RUN pip3 --no-cache-dir install --upgrade pip && \
    (cd /usr/local/geoss_search && pip3 --no-cache-dir install --prefix=/usr/local -r requirements-production.txt && pip3 --no-cache-dir install --prefix=/usr/local . && python3 setup.py clean -a)

CMD ["/usr/local/bin/docker-command.sh"]

EXPOSE 8000
EXPOSE 8443

# TESTING Image
FROM base as testing
RUN apt-get update && apt-get install -y --no-install-recommends git-lfs && apt-get clean && \
    git lfs install && git clone https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2
ENV MODEL_PATH="/paraphrase-MiniLM-L3-v2"
RUN geoss_search init tests/test_data/geoss_open_resp.json --with-schema tests/test_data/schema.yml --force

# REDIS setup
FROM base as redis-setup

COPY redis-model-store.py /usr/local/bin/modelstore
RUN chmod +x /usr/local/bin/modelstore
