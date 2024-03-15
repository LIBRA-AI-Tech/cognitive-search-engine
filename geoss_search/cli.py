import os
import logging
import click
import uvicorn
import json
import warnings
from typing import Optional, Iterator, Union
from time import perf_counter
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from tqdm import tqdm
import pandas as pd
from .model_inference import get_dims
from .settings import settings
from .enrich import enrich, bulk_predict

logging.basicConfig(level=logging.INFO)
logging.getLogger("elastic_transport.transport").setLevel(logging.WARNING)

@click.group()
def cli() -> None:
    """Auxiliary commands for GEOSS search service"""
    pass

@cli.command()
@click.option('--host', default="0.0.0.0", type=str, help="Bind socket to this host.", show_default=True,)
@click.option('--port', default=8000, type=int, help="Bind socket to this port.", show_default=True,)
@click.option('--reload', is_flag=True, default=False, type=bool, help="Enable auto-reload.",)
@click.option('--workers', default=1, type=int, help="Number of worker processes.", show_default=True,)
@click.option(
    '--timeout-keep-alive',
    default=5,
    type=int,
    help="Close Keep-Alive connections if no new data is received within this timeout",
    show_default=True,
)
def run(**kwargs) -> None:
    """Serve application through the uvicorn ASGI web server"""
    uvicorn.run("geoss_search:app", **kwargs)

async def _load_json(filename: str, **kwargs) -> Iterator[dict]:
    """Lazy loads a json file.

    Create an iterator for a JSON file and returns enriched entries with
    vector embedding and WKT bounding box.

    Args:
        filename (str): Path of the JSON file (with filename)

    Yields:
        dict: Enriched entry
    """
    with open(filename, 'r') as open_file:
        for report in tqdm(json.load(open_file).get('reports')):
            yield enrich(report, **kwargs)

class Cache:
    """Auxiliary class to cache DataFrame groups"""

    def __init__(self) -> None:
        self._cache = {}

    def get(self, src: str, title: str, desc: str) -> Optional[str]:
        """Get the group of a record

        Args:
            src (str): Source organization
            title (str): Title
            desc (str): Description

        Returns:
            Optional[str]: Group identifier if group exists; None otherwise
        """
        cache = self._cache
        if src in cache and title in cache[src] and desc in cache[src][title]:
            return cache[src][title][desc]
        return None

    def update(self, src: str, title: str, desc: str, value: str) -> None:
        """Update information with a new record

        Args:
            src (str): Source organization
            title (str): Title
            desc (str): Description
            value (str): Group identifier
        """
        if src in self._cache:
            if title in self._cache[src]:
                self._cache[src][title][desc] = value
            else:
                self._cache[src][title] = {desc: value}
        else:
            self._cache[src] = {src: {title: {desc: value}}}

def load_parquet(es: Elasticsearch, elastic_index: str, filename: str, **kwargs) -> Iterator[dict]:
    """Load a parquet file into a Pandas DataFrame

    An additional attribute `group` is added in the DataFrame, which is populated with a
    uuid value, indicating the same groups in the dataset.

    Args:
        es (elasticsearch.Elasticsearch): Elasticsearch engine
        elastic_index (str): Elastic index of the data
        filename (str): Path of the parquet file.

    Yields:
        Iterator[dict]: Dictionary represantation of each record (row).
    """
    from uuid import uuid4
    df = pd.read_parquet(filename)
    df = bulk_predict(df, **kwargs)
    cache = Cache()
    for _, row in df.iterrows():
        record = row.to_dict()
        src = row.source['id']
        title = row.title
        desc = row.description
        if desc is not None and desc.strip() == '':
            desc = None
            record['description'] = None
        group = cache.get(src, title, desc)
        if group is not None:
            record['_group'] = group
        else:
            query = {
                "bool": {
                    "filter": [
                        {
                            "match_phrase": { "title": title }
                        },
                        {
                            "term": { "source.id": src }
                        }
                    ]
                }
            }
            if desc is not None:
                query['bool']['filter'].append({"match_phrase": {"description": desc}})
            else:
                query['bool']['filter'].append({"bool": {"must_not": {"exists": {"field": "description"}}}})
            try:
                result = es.search(
                    index=elastic_index,
                    query=query,
                    source=['_group'],
                    size=1
                )
            except Exception as e:
                logging.warn(query)
                raise e
            try:
                group = result['hits']['hits'][0]['_source']['_group']
            except IndexError:
                group = str(uuid4())
            cache.update(src, title, desc, group)
            record["_group"] = group
        yield record

def _get_schema_mappings(with_schema: Optional[str]=None) -> dict:
    """Retrieve the Elastic schema according to the given definition, enriched by the required fields

    Args:
        with_schema (Optional[str], optional): Path of the schema YAML file. Defaults to None.

    Returns:
        dict: Schema definition.
    """
    import yaml
    if not os.path.isfile(with_schema):
        raise ValueError("`with_schema` parameter does not correspond to file")
    if with_schema is not None:
        with open(with_schema, 'r') as stream:
            try:
                schema = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                warnings.warn('Unable to read YAML schema file')
                schema = {}
    else:
        schema = {}
    similarity = 'dot_product' if os.getenv('MODEL_NORMALIZED') == 'true' else 'cosine'
    schema['_embedding'] = {
        "type": "dense_vector",
        "dims": get_dims(),
        "index": True,
        "similarity": similarity,
    }
    schema['_geom'] = {
        "type": "geo_shape",
        "index": True,
        "ignore_malformed": True,
    }
    schema['_group'] = {
        "type": "keyword",
        "index": True,
    }
    return {
        "mappings": {
            "properties": schema
        }
    }        

def _ingest(es, path: str, elastic_index: str, embeddings: str=None) -> None:
    """Ingest data to elastic search

    Args:
        path (str): Path of data file(s); JSON and parquet files are supported.
        elastic_index (str): Elastic index that data will be ingested
        embeddings (str): Name of the embedding attribute in data file; when omitted, embedding of each record will be computed.
    """
    if not os.path.exists(path):
        raise ValueError(f'{path} does not exist.')

    files = [os.path.join(path, file) for file in os.listdir(path)] if os.path.isdir(path) else [path]
    for file in files:
        if os.path.isdir(file):
            _ingest(file, elastic_index, embeddings=embeddings)
        if file.endswith('.json'):
            logging.info('Ingesting JSON file ' + os.path.basename(file))
            bulk(es, _load_json(path, embeddings=embeddings), index=elastic_index)
        elif file.endswith('.parquet'):
            logging.info('Ingesting Parquet file ' + os.path.basename(file))
            try:
                st = perf_counter()
                info = bulk(es, load_parquet(es, elastic_index, path, embeddings=embeddings),
                    index=elastic_index,
                    raise_on_error=False,
                    raise_on_exception=False,
                    max_retries=100,
                    request_timeout=360
                )
                logging.info("Bulk result: %s", info)
                ingest_time = perf_counter() - st
                logging.info(f"Ingested Parquet in {ingest_time} s")
            except Exception as e:
                logging.exception("Ingest failed")
                raise e
        else:
            logging.info(f'{os.path.basename(file)} type is not supported.')
            continue

def _create_elastic_index(es, index: str, with_schema: Optional[Union[str, dict]]=None, force: bool=False) -> bool:
    """Create an index to ElasticSearch

    Creates the index used by the service, the name of the index
    is determined in the configuration of the application.

    index (str): Index name
    with_schema (Optional[Union[str, dict]], optional): A mappings dictionary, or path of a YAML file with schema information. Defaults to None.
    force (bool, optional): When True, ingests data to ElasticSearch even if database is not empty
        (removes index before ingesting). Defaults to False.

    Returns:
        bool: True when index is created; False otherwise (i.e. index already exists and force is False).
    """
    if (not force):
        if es.indices.exists(index=index):
            logging.info(f"Index {index} already exists.")
            return False
    else:
        es.indices.delete(index=index, ignore=[400, 404])
    mappings = with_schema if isinstance(with_schema, dict) else _get_schema_mappings(with_schema=with_schema)
    es.indices.create(body=mappings, index=index, ignore=[400, 404])
    logging.info(f"Created index {index}")
    return True

@cli.command()
@click.option('--with-schema', type=click.Path(exists=True), help="Metadata schema according to ElasticSearch specification",)
@click.option('--force', is_flag=True, default=False, help="Force index creation even in case index already exists (all data in the existing index will be lost!)")
def create_elastic_index(**kwargs):
    """Initialize ElasticSearch by creating the elastic index."""
    es = Elasticsearch(
        os.getenv("ELASTIC_NODE"),
        ca_certs=os.path.join(os.getenv('CA_CERTS'), 'ca.crt'),
        basic_auth=("elastic", os.getenv('ELASTIC_PASSWORD')),
        request_timeout=360,
    )
    _create_elastic_index(es, settings.elastic_index, **kwargs)
    properties = {
        "started": {"type": "date"},
        "finished": {"type": "date"},
        "reset_index": {"type": "boolean"},
        "records": {"type": "integer"},
        "status": {"type": "keyword"},
        "progress": {"type": "text"},
    }
    _create_elastic_index(es, 'ingest-jobs', with_schema={"mappings": {"properties": properties}})
    properties = {
        "recordId": {"type": "keyword"},
        "assetType": {"type": "keyword"},
        "driver": {"type": "text"},
        "insights": {"type": "text", "index": "false"}
    }
    _create_elastic_index(es, 'data-insights', with_schema={"mappings": {"properties": properties}})
    properties = {
        "recordId": {"type": "keyword"},
        "results": {"properties": {
            "recordId": {"type": "keyword"},
            "results": {
                "properties": {
                    "title": {"type": "text", "index": "false"},
                    "link": {"type": "text", "index": "false"},
                    "description": {"type": "text", "index": "false"}
                }
            }
        }}
    }
    _create_elastic_index(es, 'google-search', with_schema={"mappings": {"properties": properties}})

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--embeddings', default=None, help="Name of the embedding attribute in data file(s); when omitted, embedding of each record will be computed.")
@click.option('--reset', is_flag=True, default=False, help="Force index creation even in case index already exists (all data in the existing index will be lost!)")
@click.option('--with-schema', type=click.Path(exists=True), help="Metadata schema according to ElasticSearch specification",)
def ingest(path: str, **kwargs) -> None:
    """Ingest data into Elastic index.

    Args:
        path (str): Path to data file(s)
    """
    es = Elasticsearch(
        os.getenv("ELASTIC_NODE"),
        ca_certs=os.path.join(os.getenv('CA_CERTS'), 'ca.crt'),
        basic_auth=("elastic", os.getenv('ELASTIC_PASSWORD')),
        request_timeout=360,
    )
    reset = kwargs.pop('reset', False)
    with_schema = kwargs.pop('with_schema', None)
    if reset:
        _create_elastic_index(es, settings.elastic_index, force=reset, with_schema=with_schema)
    _ingest(es, path, **kwargs)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-i', '--index', default="data-insights", type=str)
def import_parquet(path: str, index: str):
    df = pd.read_parquet(path, engine="pyarrow")
    es = Elasticsearch(
        os.getenv("ELASTIC_NODE"),
        ca_certs=os.path.join(os.getenv('CA_CERTS'), 'ca.crt'),
        basic_auth=("elastic", os.getenv('ELASTIC_PASSWORD')),
        request_timeout=360,
    )
    def _load_imported_parquet():
        for _, row in tqdm(df.iterrows(), total=df.shape[0]):
            yield row.to_dict()
    info = bulk(es, _load_imported_parquet(),
        index=index,
        raise_on_error=False,
        raise_on_exception=False,
        max_retries=100,
        request_timeout=360
    )

if __name__ == "__main__":
    cli()
