from datetime import datetime
from fastapi import APIRouter, Depends

from geoss_search.settings import settings
from geoss_search.elastic import Query as ElasticQuery
from geoss_search.schemata.general import IngestBody
from geoss_search.tasks import ingest_data_task

from ..dependencies import es, api_key_auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(api_key_auth)]
)

@router.post('/ingest', summary="Ingest data into ElasticSearch", status_code=202)
async def ingest(ingestBody: IngestBody):
    elastic_index = settings.elastic_index if ingestBody.elastic_index is None else ingestBody.elastic_index
    response = await es.index(index='ingest-jobs', body={"started": datetime.now().isoformat(), "status": "pending", "elastic_index": elastic_index})
    token = response.get('_id')
    ingest_data_task.apply_async((ingestBody.path, ingestBody.embeddings, elastic_index), task_id=token)
    return {"token": token, "url": f"/task/{token}"}

@router.get('/task/{token}', summary="Get task info")
async def get_task_info(token: str):
    details = await ElasticQuery(es=es, index="ingest-jobs").query({"ids": {"values": [token]}}).exec()
    details = details['hits']['hits']
    if len(details) == 0:
        return None
    details = details[0].get('_source', {})
    return details
