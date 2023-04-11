from fastapi import FastAPI
import os
import redis

from geoss_search.settings import settings
from geoss_search.schemata.general import HealthResults
from geoss_search._version import __version__

from .internal import admin
from .routers import search
from .dependencies import es

app = FastAPI(
    title="GEOSS cognitive search API",
    description="GEOSS metadata catalog, supporting cognitive search",
    version=__version__,
    root_path=os.getenv('ROOT_PATH', '/')
)
app.include_router(admin.router)
app.include_router(search.router)
redis_pool = redis.ConnectionPool(host='redisai', port=6379, db=0)

@app.on_event("shutdown")
async def app_shutdown():
    """Close connection to elastic search on application shutdown"""
    await es.close()

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
