import os
from fastapi import APIRouter, Query

from geoss_search.elastic import SemanticSearch
from geoss_search.schemata.sort_and_filter import SemanticFilterResponse, SemanticSortBody, SemanticSortResponse
from ..dependencies import es

router = APIRouter(
    prefix="/semantic",
    tags=["Semantic"],
)

@router.get('/filter', response_model=SemanticFilterResponse, summary="Sort and filter approach", description="Perform a semantic search based on the provided query, returning a list of record IDs with similarity score above the given threshold.")
async def filter_query(
    query: str = Query(..., description="Query string for semantic search. Search is performed in *title*, *description*, and *keyword* attributes of metadata.", example="inland water pollution"),
    threshold: float = Query(os.getenv('SORT_FILTER_THRESHOLD', 0.7), description="Threshold for cosine similarity search; a value between 0 and 1", le=1.0, ge=0.0)
):
    handler = SemanticSearch(es=es)
    handler = handler.query(query)
    handler = handler.recordsPerPage(10000).minScore(threshold)._source(["id"])
    response = await handler.exec()
    size = response['hits']['total']['value']
    max_score = response['hits']['max_score']
    results = [{'id': r['_source']['id'], 'score': r['_score']} for r in response['hits']['hits']] if size > 0 else []
    return {'size': size, 'maxScore': max_score, 'results': results}

@router.post('/sort', response_model=SemanticSortResponse, summary="Filter and sort approach", description="Sort records given a list of IDs and a query")
async def sort_query(body: SemanticSortBody):
    handler = SemanticSearch(es=es)
    handler = handler.query(body.query)
    handler = handler.filter("id", body.ids)
    handler = handler.recordsPerPage(10000)._source(["id"])
    response = await handler.exec()
    size = response['hits']['total']['value']
    results = [{'id': r['_source']['id'], 'score': r['_score']} for r in response['hits']['hits']] if size > 0 else []
    return {'query': body.query, 'sorted': results}
