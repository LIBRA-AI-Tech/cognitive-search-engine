import os
import json
import asyncio
import aiohttp
import pygeos as pg
from geoss_search.elastic import Query as ElasticQuery
from geoss_search.api.dependencies import es
from .google_search import GoogleSearch

async def spatial_context(geom):
    area_threshold = 200
    area = pg.area(pg.polygons(geom['coordinates'])[0]) if geom['type'] == 'Polygon' else 0
    if area > area_threshold:
        return None
    if geom['type'] == 'Polygon':
        polygon = ';'.join([','.join(map(str, p)) for p in geom['coordinates'][0]])
        params = {'polygon': polygon}
    else:
        try:
            point = ','.join([str(c) for c in geom['coordinates']])
        except Exception as e:
            print(str(e))
        params = {'point': point}

    headers = {"Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(os.getenv('SPATIAL_CONTEXT_URL'), params=params, headers=headers, timeout=30) as resp:
                external = await resp.json() if resp.status == 200 else None
        except asyncio.TimeoutError:
            external = None
        except Exception as e:
            print(str(e))

    return external

async def get_insights(id_):
    handler = ElasticQuery(es=es, index="data-insights")
    handler = handler.query({
        "term": {"recordId": {"value": id_}}
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
    return insights

async def get_google_results(id_: str, description: str):
    handler = ElasticQuery(es=es, index="google-search")
    handler = handler.query({
        "term": {"recordId": {"value": id_}}
    })
    response = await handler.exec()
    if len(response['hits']['hits']) == 0:
        gs = GoogleSearch()
        gresults = await gs.search(description)
    else:
        gresults = response['hits']['hits'][0]['_source']['results']
    return gresults