import click
import uvicorn
import json
import asyncio
import warnings
from .model_inference import get_dims
from .elastic import engine_connect, async_bulk
from .settings import settings
from .enrich import enrich

@click.group()
def cli() -> None:
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
    uvicorn.run("geoss_search:app", **kwargs)

async def _load_json(filename):
    from tqdm import tqdm
    with open(filename, 'r') as open_file:
        for report in tqdm(json.load(open_file).get('reports')):
            yield enrich(report)

async def _ingest(path, with_schema=None, force=False):
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
    await async_bulk(es, _load_json(path), index=settings.elastic_index)
    await es.close()

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--with-schema', type=click.Path(exists=True), help="Metadata schema according to ElasticSearch specification",)
@click.option('--force', is_flag=True, default=False, help="Force data ingestion even if index exists.")
def init(path, **kwargs) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_ingest(path, **kwargs))

if __name__ == "__main__":
    cli()
