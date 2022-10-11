from fastapi import FastAPI, Query
from datetime import datetime
from typing import List, Optional
import math
import pygeos as pg
import json
import numpy as np
from .settings import settings
from .elastic import Aggregation, engine_connect, SemanticSearch, ExactSearch
from .schemata.general import ListOfRecords, SearchResults, HealthResults, SourceSchema, RawMetadata, QueryMethod, SpatialPredicate, Attributes
from ._version import __version__

es = engine_connect()
app = FastAPI(title="GEOSS cognitive search API", description="GEOSS metadata catalog, supporting cognitive search", version=__version__)

@app.on_event("shutdown")
async def app_shutdown():
    """Close connection to elastic search on application shutdown"""
    await es.close()

def _getFeatures(field):
    id_, geom, group_id = field
    feature = {'type': 'Feature', 'id': id_}
    try:
        geometry = json.loads(pg.to_geojson(pg.from_wkt(geom)))
    except:
        geometry = None
    if geometry is not None:
        feature['geometry'] = geometry
    feature['properties'] = {'groupId': group_id}
    return feature
_getFeatures = np.vectorize(_getFeatures, signature='(m)->()')

def _parseElasticResponse(response: dict, **kwargs) -> dict:
    page = kwargs.pop('page', 1)
    totalPages = math.ceil(response['hits']['total']['value'] / kwargs.pop('records_per_page', 10))
    numberOfResults = response['hits']['total']['value']
    data = [{
        'groupId': hit['fields']['_group'][0],
        'memberCount': hit['inner_hits']['grouped']['hits']['total']['value'],
        'members': [member['_source']['id'] for member in hit['inner_hits']['grouped']['hits']['hits']],
        'title': hit['fields'].get('title', [''])[0],
        'description': hit['fields'].get('description', [''])[0],
        'origOrgId': hit['fields'].get('origOrgId', [''])[0],
        'origOrgDesc': hit['fields'].get('origOrgDesc', [''])[0],
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
            {'term': values['source_title']['buckets'][0]['key'], 'freq': values.get('doc_count'), 'termId': values.get('key')} for values in properties['buckets']]
        for termtype, properties in response['aggregations'].items()
    }
    geoms = np.array([
        (inner_hit['_source']['id'], inner_hit['_source']['_geom'][0], hit['fields']['_group'][0]) 
            for hit in response['hits']['hits'] 
            for inner_hit in hit['inner_hits']['grouped']['hits']['hits']
    ])
    features = _getFeatures(geoms)
    geojson = {'type': 'FeatureCollection', 'features': features.tolist()}
    return {'page': page, 'totalPages': totalPages, 'numberOfResults': numberOfResults, 'data': data, 'significantTerms': significantTerms, 'geoJson': geojson}

@app.get('/search', response_model=SearchResults, summary="Perform a search on GEOSS metadata")
@app.get('/search', summary="Perform a search on GEOSS metadata")
async def search(
    query: str=Query(None, description="Query string for semantic or exact search (the method used is determined by the value of the `queryMethod` parameter). Search is performed in *title*, *description*, and *keyword* attributes of metadata. In case of exact search, multiple search terms are allowed, separated by `AND` or `OR`.", example="sustainability"),
    query_method: QueryMethod=Query("semantic", alias="queryMethod", title="Query Method", description="Determines the method applied to search for the query term(s) in metadata attributes."),
    min_score: float=Query(0, alias="minScore", title="Minimum Score", description="Only results with a relevance score larger than this value will be included to the response."),
    page: int=Query(1, description="Requested page of results"),
    records_per_page: int=Query(10, alias="recordsPerPage", description="Number of groups returned in each page", le=100),
    bbox: str=Query(None, title="Bounding Box", description="[**FILTER**] A bounding box (expressed in EPSG:4326); comma separated list of (float) values: west,south,east,north", example="-11.5,35.3,43.2,81.4"),
    spatial_predicate: SpatialPredicate=Query("overlaps", alias="spatialPredicate", title="Spatial predicate", description="Spatial bounding box predicate."),
    sources: str=Query(None, description="[**FILTER**] Comma separated list of DAB sources identifiers; only records come from these sources will be included.", example="copernicuscamsid"),
    time_start: datetime=Query(None, alias="timeStart", title="Time start", description="[**FILTER**] Date or datetime expressed in ISO8601 format; only records with a time extend **after** this date will be included", examples={"date": {"value": "2018-01-01", "summary": "Date only"}, "datetime": {"value": "2018-01-01T00:00:00Z", "summary": "Datetime"}}),
    time_end: datetime=Query(None, alias="timeEnd", title="Time end", description="[**FILTER**] Date or datetime expressed in ISO8601 format; only records with a time extend **before** this date will be included", examples={"date": {"value": "2018-12-31", "summary": "Date only"}, "datetime": {"value": "2018-12-31T23:59:59Z", "summary": "Datetime"}}),
    keyword: str=Query(None, description="[**FILTER**] Only records which have been assigned at least with one of those keywords will be returned.", example="Field Observation"),
    format: str=Query(None, title="Dataset Format", description="[**FILTER**] Only records with dataset format included in this list will be returned.", example="WaterML 2.0"),
    protocol: str=Query(None, title="Online Rerource Protocol", description="[**FILTER**] Only records with online resources in one of these protocols will be included.", example="FTP"),
    organisation_name: str=Query(None, alias="organisationName", title="Organisation Name", description="[**FILTER**] Only records with originator organisation name included in this list will be returned.", example="GFZ Potsdam"),
    geoss_data_core: bool=Query(False, alias="geossDataCore", title="GEOSS Data Core", description="[**FILTER**] When True, only records that include GEOSS Data Core rights will be returned."),
    terms_size: int=Query(50, alias="termsSize", title="Terms size", description="Determines the number of results in the terms frequencies"),
    terms_significance: bool=Query(True, alias="termsSignificance", title="Significance", description="When True, terms' frequencies are sorted by a score reflecting their significance in the specific query, taking into account the terms appearance in the background of the query. Otherwise, they are sorted only by their frequency in the query results."),
) -> None:
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
    handler = SemanticSearch(es=es) if query_method == 'semantic' else ExactSearch(es=es)
    handler = handler.query(query).page(page).recordsPerPage(records_per_page).minScore(min_score) \
        .fields(["title", "description", "origOrgId", "origOrgDesc"]) \
        ._source("false") \
        .collapse({
            "field": "_group",
            "inner_hits": {
                "name": "grouped",
                "size": 1,
                "_source": ["id", "_geom"]
            }
        })
    if bbox is not None:
        handler = handler.bbox(bbox, predicate=spatial_predicate)
    if time_start is not None or time_end is not None:
        handler = handler.between(from_=time_start, to_=time_end)

    for key, value in {'source.id': sources, 'keyword': keyword, 'format': format, 'online.protocol': protocol, 'origOrgDesc': organisation_name}.items():
        if value is None:
            continue
        terms = value.split(',')
        if len(terms) == 1:
            terms = terms[0]
        handler = handler.filter(key, terms)
    if (geoss_data_core):
        handler = handler.filter('rights', 'geossdatacore')
    
    for name, field in {'keyword': 'keyword', 'format': 'format', 'protocol': 'online.protocol', 'organisation': 'origOrgDesc', 'source': 'source.id'}.items():
        agg = Aggregation()
        agg_type = 'significant_terms' if terms_significance else 'terms'
        agg.add(name, agg_type, field, size=terms_size)
        if name == 'source':
            agg.add('source_title', 'terms', 'source.title', size=1)
        handler = handler.aggs(agg)
    agg = Aggregation().add('group_number', 'cardinality', '_group')
    handler = handler.aggs(agg)

    response = await handler.exec()

    return _parseElasticResponse(response, page=page, records_per_page=records_per_page, terms_significance=terms_significance)

@app.get('/sources', response_model=List[SourceSchema], summary="Retrieve available sources list")
async def sources():
    """Fetch a list of all available sources of GEOSS metadata"""

@app.get('/raw', response_model=RawMetadata, summary="Retrieve raw metadata for specific record")
async def raw(
    id: str=Query(..., description="Resource id"),
):
    """Get raw metadata for a specific record, given its ID"""

@app.get('/metadata', response_model=ListOfRecords, summary="Retrieve metadata for a list of record IDs")
async def metadata(
    ids: str=Query(..., description="A comma separated list of resource IDs"),
    attributes: Optional[List[Attributes]]=Query(['id', 'title', 'description', 'source', 'online', 'keyword'], description="List of attributes that will be included in the response.")
):
    """Get metadata for a comma separated list of records, given their IDs"""

@app.get('/health', response_model=HealthResults, summary="Service health")
async def health():
    """Check the health of the service"""
    try:
        health = await es.cluster.health()
    except Exception as e:
        return {"status": "FAILED", "details": "Connection to search engine failed", "message": str(e)}
    if health["status"] != 'green':
        return {"status": "FAILED", "details": "Search engine status is {}".format(health["status"]), "message": ""}
    if health["number_of_nodes"] != 3:
        return {"status": "OK", "details": "", "message": "Currently {} nodes are running".format(health["number_of_nodes"])}
    index_exists = await es.indices.exists(index=settings.elastic_index)
    if not index_exists:
        return {"status": "FAILED", "details": "Index `{}` does not exist in search engine".format(settings.elastic_index), "message": ""}
    return {"status": "OK", "details": "", "message": "System is running healthy"}
