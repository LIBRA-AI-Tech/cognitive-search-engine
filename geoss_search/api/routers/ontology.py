from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from elasticsearch.exceptions import NotFoundError

from geoss_search.settings import settings
from geoss_search.schemata.ontology import SingleOntologyResponse, NewOntology, UpdateOntology

from ..dependencies import es, api_key_auth

router = APIRouter(
    prefix="/ontology",
    tags=["Ontology"],
    dependencies=[Depends(api_key_auth)]
)

async def _check_record_id(record_id: str) -> None:
    exists = await es.search(index=settings.elastic_index, query={"bool": {"filter": [{"term": {"id": record_id}}]}}, filter_path=['hits.total.value'])
    exists = exists['hits']['total']['value'] > 0
    if not exists:
        body = {
            "detail": [
                {
                    "loc": [
                        "body",
                        "recordId"
                    ],
                    "msg": "recordId not fount",
                    "type": "value_error.notfound"
                }
            ]
        }
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=body,
        )

@router.get('/eiffo/{record_id}', response_model=List[SingleOntologyResponse], summary="Retrieve EIFF-O ontology for a specific record")
async def ontology(record_id: str = Query(..., description="Record ID")):
    records = await es.search(
        index="ontology",
        query={"bool": {"filter": [{"term": {"record_id": record_id}}]}},
        source_includes=['ontology', 'concept', 'individual', 'description', 'creation'],
        filter_path=["hits.hits._id", "hits.hits._source"]
    )
    try:
        records = [dict(id= record['_id'], **record['_source']) for record in records['hits']['hits']]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="recordId not found"
        )
    return records

@router.post('/eiffo', response_model=SingleOntologyResponse, summary="Add EIFF-O ontology details for a specific record", status_code=status.HTTP_201_CREATED)
async def new_ontology(ontology: NewOntology):
    await _check_record_id(ontology.record_id)
    body = dict(**ontology.dict(), creation=datetime.now().isoformat())
    record = await es.index(index='ontology', body=body, filter_path=['_id'])
    return dict(id = record['_id'], **body)

@router.put('/eiffo/{entry_id}', summary="Update an individual entry for EIFF-O ontology", status_code=status.HTTP_204_NO_CONTENT)
async def update_ontology(ontology: UpdateOntology, entry_id: str = Query(..., description="Ontology entry ID")):
    fields = ontology.dict()
    fields = {f: fields.get(f) for f in fields.keys() if fields.get(f) is not None}
    try:
        await es.update(index='ontology', id=entry_id, body={"doc": fields})
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="entry id not found"
        )

@router.delete('/eiffo/{entry_id}', summary="Delete an individual entry of EIFF-O ontology", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ontology(entry_id: str = Query(..., description="Ontology entry ID")):
    try:
        await es.delete(index='ontology', id=entry_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="entry id not found"
        )
