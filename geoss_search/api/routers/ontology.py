from typing import List, Tuple, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from elasticsearch.exceptions import NotFoundError
from uuid import uuid4

from geoss_search.settings import settings
from geoss_search.schemata.ontology import SingleOntologyResponse, NewOntology, UpdateOntology

from ..dependencies import es, api_key_auth

router = APIRouter(
    prefix="/ontology",
    tags=["Ontology"],
    dependencies=[Depends(api_key_auth)]
)

async def _check_record_id(record_id: str) -> Tuple[str, List[Dict[str, str]]]:
    response = await es.search(
        index=settings.elastic_index, 
        query={"bool": {"filter": [{"term": {"id": record_id}}]}}, 
        source_includes=['_ontology'],
        filter_path=['hits.total.value', 'hits.hits']
    )
    exists = response['hits']['total']['value'] > 0
    if not exists:
        body = {
            "detail": [
                {
                    "loc": [
                        "body",
                        "recordId"
                    ],
                    "msg": "recordId not found",
                    "type": "value_error.notfound"
                }
            ]
        }
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=body,
        )
    try:
        records = response['hits']['hits'][0]['_source']['_ontology']
    except KeyError:
        records = []
    if records is None:
        records = []
    return response['hits']['hits'][0]['_id'], records

async def _get_records_by_entry_id(entry_id: str) -> Tuple[str, List[Dict[str, str]]]:
    response = await es.search(
        index=settings.elastic_index,
        query={"bool": {"filter": [{"term": {"_ontology.id": entry_id}}]}},
        source_includes=["_ontology"],
        filter_path=["hits.total.value", "hits.hits._id", "hits.hits._source"]
    )
    if response['hits']['total']['value'] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="entry id not found"
        )
    records = response['hits']['hits'][0]['_source']['_ontology']
    return response['hits']['hits'][0]['_id'], records

@router.get('/eiffo/{record_id}', response_model=List[SingleOntologyResponse], summary="Retrieve EIFF-O ontology for a specific record")
async def ontology(record_id: str = Query(..., description="Record ID")):
    records = await es.search(
        index=settings.elastic_index,
        query={"bool": {"filter": [{"term": {"id": record_id}}]}},
        source_includes=['_ontology'],
        filter_path=["hits.hits._id", 'hits.total.value', "hits.hits._source"]
    )
    if records["hits"]["total"]["value"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="recordId not found"
        )
    try:
        records = records['hits']['hits'][0]['_source']['_ontology']
    except KeyError:
        records = []
    if records is None:
        records = []
    return records

@router.post('/eiffo', summary="Add EIFF-O ontology details for a specific record", status_code=status.HTTP_201_CREATED)
async def new_ontology(ontology: NewOntology):
    body = dict(id=str(uuid4()), **ontology.dict(), creation=datetime.now().isoformat())
    record_id = body.pop('record_id')
    id_, previous = await _check_record_id(record_id)
    await es.update(index=settings.elastic_index, id=id_, body={"doc": {"_ontology": [*previous, body]}})
    return dict(**body)

@router.put('/eiffo/{entry_id}', summary="Update an individual entry for EIFF-O ontology", status_code=status.HTTP_204_NO_CONTENT)
async def update_ontology(ontology: UpdateOntology, entry_id: str = Query(..., description="Ontology entry ID")):
    fields = ontology.dict()
    fields = {f: fields.get(f) for f in fields.keys() if fields.get(f) is not None}
    id_, records = await _get_records_by_entry_id(entry_id)
    body = [{**r, **fields} if r['id'] == entry_id else r for r in records]
    await es.update(index=settings.elastic_index, id=id_, body={"doc": {"_ontology": body}})

@router.delete('/eiffo/{entry_id}', summary="Delete an individual entry of EIFF-O ontology", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ontology(entry_id: str = Query(..., description="Ontology entry ID")):
    id_, records = await _get_records_by_entry_id(entry_id)
    body = [r for r in records if r['id'] != entry_id]
    await es.update(index=settings.elastic_index, id=id_, body={"doc": {"_ontology": body}})
