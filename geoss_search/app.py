from fastapi import FastAPI, Query
from .model_inference import predict
from .settings import settings
from .elastic import engine_connect
from .schemata import SearchResults, HealthResults
from ._version import __version__

es = engine_connect()
app = FastAPI(title="GEOSS Search", description="GEOSS search with full text search", version=__version__)

@app.on_event("shutdown")
async def app_shutdown():
    """Close connection to elastic search on application shutdown"""
    await es.close()

@app.get('/', response_model=SearchResults, summary="Perform a search query")
async def search(
    query: str=Query(None, description="Query string"),
    page: int=Query(1, description="Requested page of results")
) -> None:
    """Query records using cosine similarity."""
    import math
    query_embedding = predict(query)

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.queryEmbedding, '_embedding') + 1.0",
                "params": {"queryEmbedding": query_embedding}
            }
        }
    }
    response = await es.search(
        index=settings.elastic_index,
        body={
            "min_score": 1.0,
            "from": settings.results_per_page * (page - 1),
            "size": settings.results_per_page,
            "query": script_query,
            "_source": {"includes": ["id", "title", "description"]},
        }
    )

    return {
        "page": page,
        "totalPages": math.ceil(response['hits']['total']['value'] / settings.results_per_page),
        "numberOfResults": response['hits']['total']['value'],
        "maxScore": response['hits']['max_score'],
        "data": [{**hit['_source'], 'score': hit['_score']} for hit in response['hits']['hits']]
    }

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
