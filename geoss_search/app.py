from fastapi import FastAPI, Query
from .model_inference import predict
from .settings import settings
from .elastic import engine_connect
from .schemata import SearchResults

es = engine_connect()
app = FastAPI()

@app.on_event("shutdown")
async def app_shutdown():
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

@app.get('/health', summary="Check the health of the service")
async def health():
    health = await es.cluster.health()
    return health
