from sentence_transformers import SentenceTransformer
from typing import List, Optional
import torch
import json
from fastapi import FastAPI
import numpy as np
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import requests
import time

load_dotenv()

class InputQuery(BaseModel):
    text: Optional[str] = 'climate change'


#model_class = ModelInference(args)

es = Elasticsearch([{'host': 'localhost'}])
app = FastAPI()

INDEX_NAME = os.environ['INDEX_NAME']
SEARCH_SIZE = 5

encoder_url = 'http://127.0.0.1:8000/encode'

@app.post('/query')
def search(query: InputQuery):

    embedding_start = time.time()
    res = requests.post(encoder_url, data=json.dumps({'text': query.text}))
    query_embedding = res.json()['embedding']
    embedding_time = time.time() - embedding_start

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {
                "source": "cosineSimilarity(params.query_embedding, 'embedding') + 1.0",
                "params": {"query_embedding": query_embedding}
            }
        }
    }

    search_start = time.time()
    response = es.search(
        index=INDEX_NAME,
        body={
            "size": SEARCH_SIZE,
            "query": script_query,
            "_source": {"includes": ["description"]}
        }
    )
    search_time = time.time() - search_start

    #print(response)

    print()
    print("{} total hits.".format(response["hits"]["total"]["value"]))
    print("embedding time: {:.2f} ms".format(embedding_time * 1000))
    print("search time: {:.2f} ms".format(search_time * 1000))
    for hit in response["hits"]["hits"]:
        print("id: {}, score: {}".format(hit["_id"], hit["_score"]))
        print(hit["_source"])
        print()


@app.get('/health_check')
async def run_health_check():
    return {'status': 'Healthy'}