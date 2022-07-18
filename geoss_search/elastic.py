from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from elasticsearch.client import AsyncSearchClient
import os
from .settings import settings

def engine_connect() -> AsyncElasticsearch:
    """A wrapper function for elastic engine connection

    Gives the flexibility to change the engine in one place

    Returns:
        AsyncElasticsearch: Elastic search engine
    """
    if settings.fastapi_env == 'testing' and settings.ca_certs is None:
        return AsyncElasticsearch(settings.elastic_node)
    return AsyncElasticsearch(
        settings.elastic_node,
        ca_certs=os.path.join(settings.ca_certs, 'ca.crt'),
        basic_auth=("elastic", settings.elastic_password),
    )
