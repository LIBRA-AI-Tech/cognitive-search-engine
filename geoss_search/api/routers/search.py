import os
import math
import json
from typing import List, Optional
import pygeos as pg
from fastapi import Query, Depends, APIRouter, HTTPException
import urllib3

from geoss_search.elastic import Aggregation, SemanticSearch, ExactSearch, Query as ElasticQuery
from geoss_search.schemata.general import ListOfRecords, SearchResults, SourceSchema, RawMetadata, Attributes
from geoss_search.schemata.query import QueryModel
from geoss_search.schemata.augmented import Augmented

from ..dependencies import es

router = APIRouter(
    tags=["Search"]
)

def _getFeatures(field):
    if len(field) == 0:
        return None
    id_, geom, group_id = field
    feature = {'type': 'Feature', 'id': id_}
    try:
        geometry = json.loads(pg.to_geojson(pg.from_wkt(geom[0]))) if len(geom) > 0 else None
    except:
        geometry = None
    if geometry is not None:
        feature['geometry'] = geometry
    feature['properties'] = {'groupId': group_id}
    return feature

def _parseElasticResponse(response: dict, **kwargs) -> dict:
    page = kwargs.pop('page', 1)
    totalPages = math.ceil(response['aggregations']['group_number']['value'] / kwargs.pop('records_per_page', 10))
    numberOfResults = response['hits']['total']['value']
    data = [{
        'groupId': hit['fields']['_group'][0],
        'memberCount': hit['inner_hits']['grouped']['hits']['total']['value'],
        'members': [member['_source']['id'] for member in hit['inner_hits']['grouped']['hits']['hits']],
        'title': hit['fields'].get('title', [''])[0],
        'description': hit['fields'].get('description', [''])[0],
        'origOrgId': hit['fields'].get('source.id', [''])[0],
        'origOrgDesc': hit['fields'].get('source.title', [''])[0],
        'score': hit['_score']
    } for hit in response['hits']['hits']]
    terms_significance = kwargs.pop('terms_significance', False)
    significantTerms = {
        termtype: [
            {'term': values.get('key'), 'freq': values.get('doc_count'), 'bgFreq': values.get('bg_count'), 'score': round(values.get('score', 0), 4)}
                if terms_significance and termtype != 'source' else
            {'term': values['source_title']['buckets'][0]['key'], 'freq': values.get('doc_count'), 'bgFreq': values.get('bg_count'), 'score': round(values.get('score', 0), 4), 'termId': values.get('key')}
                if terms_significance else
            {'term': values.get('key'), 'freq': values.get('doc_count')}
                if termtype != 'source' else
            {'term': values.get('source_title', {}).get('buckets', [{}])[0].get('key'), 'freq': values.get('doc_count'), 'termId': values.get('key')} for values in properties.get('buckets', [])]
        for termtype, properties in response['aggregations'].items()
    }
    geoms = [
        (inner_hit['_source']['id'], inner_hit['_source']['_geom'], hit['fields']['_group'][0]) 
            for hit in response['hits']['hits'] 
            for inner_hit in hit['inner_hits']['grouped']['hits']['hits']
    ]
    features = [_getFeatures(geom) for geom in geoms]
    geojson = {'type': 'FeatureCollection', 'features': [] if features is None else features}
    return {'page': page, 'totalPages': totalPages, 'numberOfResults': numberOfResults, 'data': data, 'significantTerms': significantTerms, 'geoJson': geojson}

@router.get('/search', response_model=SearchResults, summary="Perform a search on GEOSS metadata")
async def search(params: QueryModel = Depends(QueryModel.as_query)) -> None:
    """
    Search parameters optionally include a *query* string, a spatial *bounding box*, a *time extend*, as well as various *filters* that apply on the categorical attributes of the metadata. When a query string is given, the results are sorted by a score reflecting the metadata relevance with the query string. Two distinct methods are supported for the query: a *semantic search* and a more traditional *exact search*. The two methods result in different ranges for the values of the *relevance score*.

    The response consists mainly of three sections (see `Responses` for more details):

    #### a. Records (data)

    The records that comply with the search criteria are included in the response in groups. Each group of records should have identical values for each of the following attributes:
    - title
    - description
    - source (id).

    Grouped results are returned in pages (the number of groups per page can be adjusted).

    #### b. Significant Terms

    This section contains the frequencies of the most frequent terms for the following categorical attributes: *keyword*, *format*, *source*, *protocol*, *organisation*. The frequencies refer to the total results of the search (**not only** to the results of the specific page).

    #### c. GeoJSON

    A GeoJSON with the geometries of all the records contained in the specific page. Information about the group that each record belongs to is contained in the properties of each feature.
    """
    if (params.query is not None):
        handler = SemanticSearch(es=es) if params.query_method == 'semantic' else ExactSearch(es=es)
        handler = handler.query(params.query)
    else:
        handler = ElasticQuery(es=es)
    handler = handler.page(params.page).recordsPerPage(params.records_per_page).minScore(params.min_score) \
        .fields(["title", "description", "source.id", "source.title"]) \
        ._source("false") \
        .collapse({
            "field": "_group",
            "inner_hits": {
                "name": "grouped",
                "size": 10000,
                "_source": ["id", "_geom"]
            }
        })
    if params.bbox is not None:
        handler = handler.bbox(params.bbox, predicate=params.spatial_predicate)
    if params.time_start is not None or params.time_end is not None:
        handler = handler.between(from_=params.time_start, to_=params.time_end)

    for key, value in {
        'source.id': params.sources,
        'keyword': params.keyword,
        'format': params.format,
        'online.protocol': params.protocol,
        'origOrgDesc': params.organisation_name,
        '_ontology.ontology': params.ontology,
        '_ontology.concept': params.concept,
        '_ontology.individual': params.individual,
        '_extracted_keyword': params.extracted_keyword,
        '_extracted_filetype': params.extracted_filetype,
    }.items():
        if value is None:
            continue
        terms = value.split(',')
        if len(terms) == 1:
            terms = terms[0]
        handler = handler.filter(key, terms)
    
    for name, field in {
        'keyword': 'keyword',
        'format': 'format',
        'protocol': 'online.protocol',
        'organisation': 'origOrgDesc',
        'source': 'source.id',
        'ontology': '_ontology.ontology',
        'concept': '_ontology.concept',
        'individual': '_ontology.individual',
        'extractedKeyword': '_extracted_keyword',
        'extractedFiletype': '_extracted_filetype',
    }.items():
        agg = Aggregation()
        agg_type = 'significant_terms' if params.terms_significance else 'terms'
        agg.add(name, agg_type, field, size=params.terms_size)
        if name == 'source':
            agg.add('source_title', 'terms', 'source.title', size=1)
        handler = handler.aggs(agg)
    agg = Aggregation()
    agg.add('group_number', 'cardinality', '_group')
    handler = handler.aggs(agg)

    response = await handler.exec()

    return _parseElasticResponse(response, page=params.page, records_per_page=params.records_per_page, terms_significance=params.terms_significance)

@router.get('/sources', response_model=List[SourceSchema], summary="Retrieve available sources list")
async def sources():
    """Fetch a list of all available sources of GEOSS metadata"""
    agg = Aggregation()
    agg.add("source", "terms", "source.id", size=10000)
    agg.add("sourceTitle", "terms", "source.title", size=1)
    handler = ElasticQuery(es=es).aggs(agg)._source("false").size(0)
    response = await handler.exec()

    return [{"id": r['key'], "title": r['sourceTitle']['buckets'][0]['key']} for r in response['aggregations']['source']['buckets']]

@router.get('/raw', response_model=RawMetadata, summary="Retrieve raw metadata for specific record")
async def raw(
    id: str=Query(..., description="Resource id"),
):
    """Get raw metadata for a specific record, given its ID"""
    handler = ElasticQuery(es=es)
    handler = handler.query({
        "bool": {
            "must": [{
                "match": {"id": id}
            }]
        }
    })
    handler = handler._source({"excludes": ["_*"]})
    response = await handler.exec()

    if len(response['hits']['hits']) == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    return response['hits']['hits'][0]['_source']

@router.get('/augmented', summary="Retrieve augmented metadata for specific record")
async def augmented(
    id: str=Query(..., description="Resource id"),
):
    """Get augmented metadata for a specific record, given its ID"""
    # 1. Spatial context
    area_threshold = 200
    handler = ElasticQuery(es=es)
    handler = handler.query({
        "bool": {
            "must": [{
                "match": {"id": id}
            }]
        },
    })
    handler = handler._source(False)
    handler = handler.fields(['_geom'])
    response = await handler.exec()
    if len(response['hits']['hits']) == 0:
        raise HTTPException(status_code=404, detail="Record not found")
    
    geom = response['hits']['hits'][0]['fields']['_geom'][0]
    if geom['type'] == 'Polygon':
        area = pg.area(pg.polygons(geom['coordinates'])[0])
        if area > area_threshold:
            external = None
        else:
            polygon = ';'.join([','.join(map(str, p)) for p in geom['coordinates'][0]])
            http = urllib3.PoolManager()
            r = http.request("GET", os.getenv('SPATIAL_CONTEXT_URL'), fields={'polygon': polygon}, headers={"Content-Type": "application/json"})
            external = json.loads(r.data) if r.status == 200 else None
    else:
        external = None

    # 2. Data insights
    handler = ElasticQuery(es=es, index="data-insights")
    handler = handler.query({
        "term": {"recordId": {"value": id}}
    })
    response = await handler.exec()
    if len(response['hits']['hits']) == 0:
        insights = None
    else:
        insights = response['hits']['hits'][0]['_source']
        asset_type = insights.pop('assetType')
        driver = insights.pop('driver')
        other = json.loads(insights.pop('insights'))
        insights = {'assetType': asset_type, 'driver': driver, **other}

    # 3. Google results
    handler = ElasticQuery(es=es, index="google-search")
    handler = handler.query({
        "term": {"recordId": {"value": id}}
    })
    response = await handler.exec()
    if len(response['hits']['hits']) == 0:
        gresults = None
    else:
        gresults = response['hits']['hits'][0]['_source']['results']
    return {"insights": insights, "externalSources": external, "googleSearch": gresults}

@router.get('/metadata', response_model=ListOfRecords, response_model_exclude_unset=True, summary="Retrieve metadata for a list of record IDs")
async def metadata(
    ids: str=Query(..., description="A comma separated list of resource IDs"),
    attributes: Optional[List[Attributes]]=Query(['id', 'title', 'description', 'source', 'online', 'keyword'], description="List of attributes that will be included in the response.")
):
    """Get metadata for a comma separated list of records, given their IDs"""
    id_array = ids.split(',')
    handler = ElasticQuery(es=es)
    handler = handler.query({
        "bool": {
            "should": [{"match": {"id": id}} for id in id_array]
        }
    })
    handler = handler._source({"includes": attributes})
    handler = handler.fields(["_geom"])

    response = await handler.exec()
    total = response['hits']['total']['value']
    geoms = [json.dumps(record.get('fields', {}).get('_geom', [None])[0]) for record in response['hits']['hits']]
    bbox = pg.bounds(pg.union_all(pg.from_geojson(geoms))).tolist() if len(geoms) > 0 else None
    records = [record.get('_source') for record in response['hits']['hits']]

    return {"total": total, "bbox": bbox, "records": records}
