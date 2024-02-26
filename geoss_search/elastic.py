from typing_extensions import Self
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk, async_streaming_bulk
from elasticsearch.client import AsyncSearchClient
import os
from typing import Optional, List, Dict, Union, Set
from datetime import datetime
from .settings import settings
from .model_inference import predict

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
        request_timeout=360,
    )

class Aggregation:

    def __init__(self):
        self.aggs: list = []
        self.agg_names: list = []

    def add(self, agg_name: str, agg_type: str, field: str, size: Optional[int]=None) -> None:
        if agg_name in self.agg_names:
            raise ValueError(f"agg_name already declared")
        agg = {
            agg_name: {
                agg_type: {
                    "field": field
                }
            }
        }
        if size is not None:
            agg[agg_name][agg_type]['size'] = size
        self.aggs.append(agg)
        self.agg_names.append(agg_name)

    def to_dict(self) -> dict:
        aggs = None
        for i in range(len(self.aggs), 0, -1):
            agg = self.aggs[i - 1]
            agg_name = self.agg_names[i - 1]
            aggs = {agg_name: {**agg[agg_name], 'aggs': aggs}} if aggs is not None else {**agg}
        return aggs

class Query:

    def __init__(self, es: AsyncElasticsearch=engine_connect(), page: int=1, records: Optional[int]=None, index=settings.elastic_index) -> None:
        self._es = es
        self._index = index

        self.query_: Optional[str] = None
        self.min_score: Optional[float] = None
        self.page_: int = page
        self.records: int = records
        self.filter_: List[Dict[str, str]] = []
        self.aggregations: dict = {}
        self.timeStart: Optional[datetime] = None
        self.timeEnd: Optional[datetime] = None
        self.custom_: List[Set[Union[str, dict]]] = []

        self.sources: Optional[List[str]] = None
        self.keyword: Optional[List[str]] = None
        self.format: Optional[List[str]] = None
        self.protocol: Optional[List[str]] = None
        self.organisation: Optional[List[str]] = None

        self._payload: dict = {}

    def __getattr__(self, name):
        def wrapper(body):
            self.custom_.append((name, body))
            return self
        return wrapper

    def query(self, query: str) -> Self:
        self.query_ = query
        return self

    def minScore(self, score) -> Self:
        self.min_score = score
        return self

    def page(self, page) -> Self:
        self.page_ = page
        return self

    def recordsPerPage(self, records) -> Self:
        self.records = records
        return self

    def bbox(self, bbox: List[float], predicate: str="overlaps") -> Self:
        predicates = {
            'contains': 'WITHIN',
            'overlaps': 'INTERSECTS',
            'disjoint': 'DISJOINT',
        }
        xmin, ymin, xmax, ymax = bbox
        filter = {
            "geo_shape": {
                "_geom": {
                    "shape": {
                        "type": "envelope",
                        "coordinates": [[xmin, ymax], [xmax, ymin]]
                    },
                    "relation": predicates[predicate]
                }
            }
        }
        self.filter_.append(filter)
        return self

    def between(self, from_: datetime=None, to_: datetime=None) -> Self:
        if from_ is not None:
            filter = {
                "range": {
                    "when.to": {
                        "gte": from_.isoformat()
                    }
                }
            }
            self.filter_.append(filter)
        if to_ is not None:
            filter = {
                "range": {
                    "when.from": {
                        "lte": to_.isoformat()
                    }
                }
            }
            self.filter_.append(filter)
        return self

    def filter(self, field: str, value: Union[str, List[str]]) -> Self:
        filter_key = 'term' if isinstance(value, str) else 'terms'
        filter = {
            filter_key: {field: value}
        }
        self.filter_.append(filter)
        return self

    def aggs(self, aggregations: Union[List[Aggregation], Aggregation]) -> Self:
        if aggregations is None:
            return self
        if isinstance(aggregations, Aggregation):
            aggregations = [aggregations]
        for agg in aggregations:
            agg_dict = agg.to_dict()
            if agg_dict is not None:
                self.aggregations.update(agg_dict)
        return self

    def significantTerms(self, terms_list: List[str], significance_search: bool=True, terms_size: int=50) -> Self:
        method = "significant_terms" if significance_search else "terms"
        for field in terms_list:
            agg = {
                field: {
                    method: {
                        "field": field,
                        "size": terms_size
                    }
                }
            }
            self.aggregations.append(agg)
        return self

    def parse(self) -> dict:
        payload = self._payload

        if self.min_score is not None:
            payload["min_score"] = self.min_score
        if self.query_ is not None:
            payload["query"] = self.query_
        if self.records is not None:
            payload["from"] = self.records * (self.page_ - 1)
            payload["size"] = self.records

        for function, body in self.custom_:
            payload[function] = body

        if len(self.aggregations) > 0:
            payload['aggs'] = self.aggregations

        return payload

    async def exec(self):
        payload = self.parse()
        response = await self._es.search(
            index=self._index,
            body=payload
        )
        return response

class SemanticSearch(Query):

    def parse(self):
        if self.query_ is not None:
            self.filter("_lang", "en")
            self._payload["knn"] = {
                "field": "_embedding",
                "query_vector": predict(self.query_),
                "k": 10000,
                "num_candidates": 10000,
                "filter": self.filter_,
            }
            self.query_ = None
        return super().parse()

class ExactSearch(Query):

    def parse(self) -> dict:
        match_phrase = {
            "query": self.query_,
            "slop": 5,
            "analyzer": "standard",
            "zero_terms_query": "none"
        }
        self.query_ = {
            "bool": {
                "should": [
                    {
                        "match_phrase": {
                            "title": match_phrase
                        }
                    },
                    {
                        "match_phrase": {
                            "description": match_phrase
                        }
                    }
                ],
                "filter": self.filter_,
                "minimum_should_match": 1,
            }
        }
        return super().parse()
