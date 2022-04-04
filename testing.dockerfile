FROM python:3.8-slim-bullseye as build-stage-1

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    apt-get clean

COPY requirements.txt requirements-testing.txt ./
RUN pip3 install --no-cache-dir --prefix=/usr/local -r requirements.txt -r requirements-testing.txt


FROM python:3.8-slim-bullseye

ARG VERSION

ENV VERSION="${VERSION}"
ENV PYTHON_VERSION="3.8"
ENV PYTHONPATH="/usr/local/lib/python${PYTHON_VERSION}/site-packages"

COPY --from=build-stage-1 /usr/local /usr/local

COPY setup.py README.md requirements.txt ./
COPY geoss_search ./geoss_search
RUN pip3 install --upgrade pip && pip3 install --prefix=/usr/local .

ENV APP_NAME="geoss_search" \
    FASTAPI_ENV="testing"

ARG DEBIAN_FRONTEND=noninteractive
ARG DEBCONF_NOWARNINGS="yes"
RUN apt-get update && apt-get install -y --no-install-recommends git-lfs && apt-get clean && \
    git lfs install && git clone https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L3-v2
ENV MODEL_PATH="/paraphrase-MiniLM-L3-v2"

COPY run-nosetests.sh /
RUN chmod a+x /run-nosetests.sh
ENTRYPOINT ["/run-nosetests.sh"]
