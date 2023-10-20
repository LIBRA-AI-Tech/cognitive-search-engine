import os
from datetime import datetime
from pathlib import Path
from logging import getLogger
from celery import Celery
from celery.signals import worker_process_init, worker_shutdown
from elasticsearch import Elasticsearch
from geoss_search.cli import _create_elastic_index, _ingest

app = Celery(__name__)
app.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379")
app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")

# es = None

# @worker_process_init.connect
# def init_es(*args, **kwargs):
#     global es
es = Elasticsearch(
    os.getenv("ELASTIC_NODE"),
    ca_certs=os.path.join(os.getenv('CA_CERTS'), 'ca.crt'),
    basic_auth=("elastic", os.getenv('ELASTIC_PASSWORD')),
    request_timeout=360,
)

logger = getLogger()

@worker_shutdown.connect
def cleanup_worker(**kwargs):
    global es
    es.close()

def _update_job_status(token, **kwargs):
    es.update(index='ingest-jobs', id=token, body={"doc": kwargs})

@app.task(name="ingest-data-task", bind=True)
def ingest_data_task(self, path: str, embeddings: str, elastic_index: str):
    token = self.request.id
    try:
        _update_job_status(token, status="active")
        if not es.indices.exists(index=elastic_index):
            _create_elastic_index(es, index=elastic_index, with_schema=os.getenv('INIT_DATA_SCHEMA'))
        list_of_parquets = [f for f in Path(path).rglob('*.parquet')]
        _update_job_status(token, progress=f"0/{len(list_of_parquets)}")
        for counter, f in enumerate(list_of_parquets):
            _ingest(es, str(f), elastic_index, embeddings=embeddings)
            _update_job_status(token, progress=f"{counter + 1}/{len(list_of_parquets)}")
        _update_job_status(token, status="ingested", finished=datetime.now().isoformat())
    except Exception as e:
        logger.error(str(e), stack_info=True)
        _update_job_status(token, status="failed", msg=str(e), finished=datetime.now().isoformat())
