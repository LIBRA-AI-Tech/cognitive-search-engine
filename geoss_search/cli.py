import click
import uvicorn
import json
import asyncio
import warnings
from typing import Optional, Iterator, Union
from .model_inference import get_dims
from .elastic import engine_connect, async_bulk
from .settings import settings
from .enrich import enrich, bulk_predict, group_dataframe
import logging
import os

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
        dict: Erniched entry
    """
    from tqdm import tqdm
    with open(filename, 'r') as open_file:
        for report in tqdm(json.load(open_file).get('reports')):
            yield enrich(report, **kwargs)

async def _load_parquet(filename: str, **kwargs) -> Iterator[dict]:
    """Load a parquet file into a Pandas DataFrame

    Args:
        filename (str): Path of the parquet file.

    Yields:
        Iterator[dict]: Dictionary represantation of each record (row).
    """
    import pandas as pd
    from tqdm import tqdm
    df = pd.read_parquet(filename)
    logging.info("Grouping DataFrame, this might take some time...")
    df = group_dataframe(df)
    df = bulk_predict(df, **kwargs)
    for index, row in tqdm(df.iterrows(), total=len(df)):
        yield row.to_dict()

def _get_schema_mappings(with_schema: Optional[str]=None) -> dict:
    """Retrieve the Elastic schema according to the given definition, enriched by the required fields

    Args:
        with_schema (Optional[str], optional): Path of the schema YAML file. Defaults to None.

    Returns:
        dict: Schema definition.
    """
    import yaml
    if with_schema is not None:
        with open(with_schema, 'r') as stream:
            try:
                schema = yaml.safe_load(stream)
            except yaml.YAMLError as e:
                warnings.warn('Unable to read YAML schema file')
                schema = {}
    else:
        schema = {}
    schema['_embedding'] = {
        "type": "dense_vector",
        "dims": get_dims(),
        "index": True,
        "similarity": "cosine"
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

async def _ingest(path: str, embeddings: str=None) -> None:
    """Ingest data to elastic search

    Args:
        path (str): Path of data file(s); JSON and parquet files are supported.
        embeddings (str): Name of the embedding attribute in data file; when omitted, embedding of each record will be computed.
    """
    es = engine_connect()

    if not os.path.exists(path):
        raise ValueError(f'{path} does not exist.')

    files = [os.path.join(path, file) for file in os.listdir(path)] if os.path.isdir(path) else [path]
    for file in files:
        if os.path.isdir(file):
            await _ingest(file, embeddings=embeddings)
        if file.endswith('.json'):
            logging.info('Ingesting JSON file ' + os.path.basename(file))
            await async_bulk(es, _load_json(path, embeddings=embeddings), index=settings.elastic_index)
        elif file.endswith('.parquet'):
            logging.info('Ingesting Parquet file ' + os.path.basename(file))
            await async_bulk(es, _load_parquet(path, embeddings=embeddings),
                index=settings.elastic_index,
                raise_on_error=False,
                raise_on_exception=False,
                max_retries=100,
                request_timeout=360
            )
        else:
            logging.info(f'{os.path.basename(file)} type is not supported.')
            continue
    await es.close()

async def _create_elastic_index(index: str, with_schema: Optional[Union[str, dict]]=None, force: bool=False) -> bool:
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
    es = engine_connect()
    if (not force):
        if await es.indices.exists(index=index):
            logging.info(f"Index {index} already exists.")
            await es.close()
            return False
    else:
        await es.indices.delete(index=index, ignore=[400, 404])
    mappings = with_schema if isinstance(with_schema, dict) else _get_schema_mappings(with_schema=with_schema)
    await es.indices.create(body=mappings, index=index, ignore=[400, 404])
    logging.info(f"Created index {index}")
    await es.close()
    return True

@cli.command()
@click.option('--with-schema', type=click.Path(exists=True), help="Metadata schema according to ElasticSearch specification",)
@click.option('--force', is_flag=True, default=False, help="Force index creation even in case index already exists (all data in the existing index will be lost!)")
def create_elastic_index(**kwargs):
    """Initialize ElasticSearch by creating the elastic index."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_create_elastic_index(settings.elastic_index, **kwargs))
    properties = {
        "started": {"type": "date"},
        "finished": {"type": "date"},
        "reset_index": {"type": "boolean"},
        "records": {"type": "integer"},
        "status": {"type": "keyword"} 
    }
    loop.run_until_complete(_create_elastic_index('ingest-jobs', with_schema={"mappings": {"properties": properties}}))

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
    loop = asyncio.get_event_loop()
    reset = kwargs.pop('reset', False)
    with_schema = kwargs.pop('with_schema', None)
    if reset:
        loop.run_until_complete(_create_elastic_index(settings.elastic_index, force=reset, with_schema=with_schema))
    loop.run_until_complete(_ingest(path, **kwargs))

if __name__ == "__main__":
    cli()
