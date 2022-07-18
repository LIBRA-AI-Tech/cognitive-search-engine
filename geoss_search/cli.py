import click
import uvicorn
import json
import asyncio
import warnings
from typing import Optional
from .model_inference import get_dims
from .elastic import engine_connect, async_bulk
from .settings import settings
from .enrich import enrich, bulk_predict

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

async def _load_json(filename: str) -> dict:
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
            yield enrich(report)

async def _load_parquet(filename: str) -> dict:
    import pandas as pd
    from tqdm import tqdm
    df = pd.read_parquet(filename)
    df = bulk_predict(df)
    for index, row in tqdm(df.iterrows()):
        yield row.to_dict()
        

async def _ingest(path: str, with_schema: Optional[str]=None, force: bool=False) -> None:
    """Ingest data to elastic search

    Args:
        path (str): Path of data file; JSON and parquet files are supported.
        with_schema (Optional[str], optional): A YAML file with schema information. Defaults to None.
        force (bool, optional): When True, ingests data to ElasticSearch even if database is not empty
            (removes index before ingesting). Defaults to False.
    """
    import yaml
    es = engine_connect()
    if (not force and await es.indices.exists(index=settings.elastic_index)):
        await es.close()
        return
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
        "index": True
    }
    mappings = {
        "mappings": {
            "properties": schema
        }
    }
    await es.indices.delete(index=settings.elastic_index, ignore=[400, 404])
    await es.indices.create(body=mappings, index=settings.elastic_index, ignore=[400, 404])
    if path.endswith('.json'):
        await async_bulk(es, _load_json(path), index=settings.elastic_index)
    elif path.endswith('.parquet'):
        try:
            await async_bulk(es, _load_parquet(path), index=settings.elastic_index)
        except:
            pass
    else:
        raise Exception(f"path is not supported")
    await es.close()

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--with-schema', type=click.Path(exists=True), help="Metadata schema according to ElasticSearch specification",)
@click.option('--force', is_flag=True, default=False, help="Force data ingestion even if index exists.")
def init(path: str, **kwargs) -> None:
    """Initialize application by ingesting data

    Args:
        path (str): Path to data file
    """
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_ingest(path, **kwargs))

if __name__ == "__main__":
    cli()
