#!/bin/sh
#set -x
set -e

python_version="$(python3 -c 'import platform; print(platform.python_version())' | cut -d '.' -f 1,2)"
if [ "${python_version}" != "${PYTHON_VERSION}" ]; then
    echo "PYTHON_VERSION (${PYTHON_VERSION}) different with version reported from python3 executable (${python_version})" 1>&2 && exit 1
fi

export LOGGING_FILE_CONFIG="./logging.conf"
if [ ! -f "${LOGGING_FILE_CONFIG}" ]; then
    echo "LOGGING_FILE_CONFIG (configuration for Python logging) does not exist!" 1>&2 && exit 1
fi

if [ -n "${LOGGING_ROOT_LEVEL}" ]; then
    sed -i -e "/^\[logger_root\]/,/^\[.*/ { s/^level=.*/level=${LOGGING_ROOT_LEVEL}/ }" ${LOGGING_FILE_CONFIG}
fi

echo "Creating elastic index..."
geoss_search create-elastic-index --with-schema ${INIT_DATA_SCHEMA}

num_workers="4"
num_threads="1"
server_port="8000"
timeout="2"
export WORKER_CLASS=${WORKER_CLASS:-"uvicorn.workers.UvicornWorker"}

exec gunicorn --access-logfile - \
    --worker-tmp-dir /dev/shm \
    --workers ${num_workers} \
    --threads ${num_threads} \
    -t 30 \
    -k "$WORKER_CLASS" \
    --bind "0.0.0.0:${server_port}" \
    "geoss_search:app"
