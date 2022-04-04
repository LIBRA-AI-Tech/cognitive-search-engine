from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from elasticsearch.client import AsyncSearchClient
from .settings import settings

def engine_connect():
    if settings.fastapi_env == 'testing' and settings.ca_certs is None:
        return AsyncElasticsearch(settings.elastic_node)
    return AsyncElasticsearch(
        settings.elastic_node,
        ca_certs=settings.ca_certs,
        basic_auth=("elastic", settings.elastic_password),
    )
