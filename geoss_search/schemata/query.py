import inspect
from pydantic import BaseModel, ValidationError, validator, Field
from fastapi import Query
from fastapi.exceptions import RequestValidationError
from datetime import datetime
from typing import Optional
from .general import QueryMethod, SpatialPredicate

class QueryBaseModel(BaseModel):
    """Query Base class; useful to pass Validation error to client."""
    def __init_subclass__(cls, *args, **kwargs):
        field_default = Query(...)
        new_params = []
        for field in cls.__fields__.values():
            default = field.default if not field.required else field_default
            annotation = inspect.Parameter.empty

            new_params.append(
                inspect.Parameter(
                    field.alias,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=default,
                    annotation=annotation,
                )
            )

        async def _as_query(**data):
            try:
                return cls(**data)
            except ValidationError as e:
                raise RequestValidationError(e.raw_errors)

        sig = inspect.signature(_as_query)
        sig = sig.replace(parameters=new_params)
        _as_query.__signature__ = sig  # type: ignore
        setattr(cls, "as_query", _as_query)

    @staticmethod
    def as_query(parameters: list) -> "QueryBaseModel":
        raise NotImplementedError

class QueryModel(QueryBaseModel):
    query: Optional[str]=Field(Query(
        None,
        description="Query string for semantic or exact search (the method used is determined by the value of the `queryMethod` parameter). Search is performed in *title*, *description*, and *keyword* attributes of metadata. In case of exact search, multiple search terms are allowed, separated by `AND` or `OR`.",
        example="sustainability",
    ))
    query_method: QueryMethod=Field(Query(
        "semantic",
        alias="queryMethod",
        title="Query Method",
        description="Determines the method applied to search for the query term(s) in metadata attributes.",
    ))
    min_score: float=Field(Query(
        0.6,
        alias="minScore",
        title="Minimum Score",
        description="Only results with a relevance score larger than this value will be included to the response.",
    ))
    page: int=Field(Query(
        1,
        description="Requested page of results",
    ))
    records_per_page: int=Field(Query(
        10,
        alias="recordsPerPage",
        description="Number of groups returned in each page",
    ))
    bbox: Optional[str]=Field(Query(
        None,
        title="Bounding Box",
        description="[**FILTER**] A bounding box (expressed in EPSG:4326); comma separated list of (float) values: west,south,east,north",
        example="-11.5,35.3,43.2,81.4",
    ))
    spatial_predicate: SpatialPredicate=Field(Query(
        "overlaps",
        alias="spatialPredicate",
        title="Spatial predicate",
        description="Spatial bounding box predicate.",
    ))
    sources: Optional[str]=Field(Query(
        None,
        description="[**FILTER**] Comma separated list of DAB sources identifiers; only records come from these sources will be included.",
        example="copernicuscamsid",
    ))
    time_start: Optional[datetime]=Field(Query(
        None,
        alias="timeStart",
        title="Time start",
        description="[**FILTER**] Date or datetime expressed in ISO8601 format; only records with a time extend **after** this date will be included",
        examples={"date": {"value": "2018-01-01", "summary": "Date only"}, "datetime": {"value": "2018-01-01T00:00:00Z", "summary": "Datetime"}},
    ))
    time_end: Optional[datetime]=Field(Query(
        None,
        alias="timeEnd",
        title="Time end",
        description="[**FILTER**] Date or datetime expressed in ISO8601 format; only records with a time extend **before** this date will be included",
        examples={"date": {"value": "2018-12-31", "summary": "Date only"}, "datetime": {"value": "2018-12-31T23:59:59Z", "summary": "Datetime"}},
    ))
    keyword: Optional[str]=Field(Query(
        None,
        description="[**FILTER**] Only records which have been assigned at least with one of those keywords will be returned.",
        example="Field Observation",
    ))
    format: Optional[str]=Field(Query(
        None,
        title="Dataset Format",
        description="[**FILTER**] Only records with dataset format included in this list will be returned.",
        example="WaterML 2.0",
    ))
    protocol: Optional[str]=Field(Query(
        None,
        title="Online Rerource Protocol",
        description="[**FILTER**] Only records with online resources in one of these protocols will be included.",
        example="FTP",
    ))
    organisation_name: Optional[str]=Field(Query(
        None,
        alias="organisationName",
        title="Organisation Name",
        description="[**FILTER**] Only records with originator organisation name included in this list will be returned.",
        example="GFZ Potsdam",
    ))
    ontology: Optional[str]=Field(Query(
        None,
        title="Ontology",
        description="[**FILTER**] Only records with the specific ontology will be returned",
        example="sdg"
    ))
    concept: Optional[str]=Field(Query(
        None,
        title="Ontology Concept",
        description="[**FILTER**] Only records with the specific ontology concept will be returned",
        example="goal"
    ))
    individual: Optional[str]=Field(Query(
        None,
        title="Ontology Individual",
        description="[**FILTER**] Only records with the specific ontology individual will be returned",
        example="http://metadata.un.org/sdg/1"
    ))
    extracted_keyword: Optional[str]=Field(Query(
        None,
        alias="extractedKeyword",
        description="[**FILTER**] Only records including the specific extracted keywords will be returned",
        example="climate change"
    ))
    extracted_filetype: Optional[str]=Field(Query(
        None,
        alias="extractedFiletype",
        description="[**FILTER**] Only records with online sources including the specific file types will be returned",
        example="pdf"
    ))
    geoss_data_core: bool=Field(Query(
        False,
        alias="geossDataCore",
        title="GEOSS Data Core",
        description="[**FILTER**] When True, only records that include GEOSS Data Core rights will be returned.",
    ))
    terms_size: int=Field(Query(
        50,
        alias="termsSize",
        title="Terms size",
        description="Determines the number of results in the terms frequencies",
    ))
    terms_significance: bool=Field(Query(
        True,
        alias="termsSignificance",
        title="Significance",
        description="When True, terms' frequencies are sorted by a score reflecting their significance in the specific query, taking into account the terms appearance in the background of the query. Otherwise, they are sorted only by their frequency in the query results.",
    ))

    @validator('bbox')
    def bboxValidation(cls, bbox):
        if bbox is None:
            return bbox
        bbox = bbox.split(',')
        if len(bbox) != 4:
            raise ValueError('Wrong number of coordinates')
        try:
            bbox = [float(coord) for coord in bbox]
        except:
            raise ValueError('Non-numeric values encountered')
        xmin, ymin, xmax, ymax = bbox
        xmin, xmax = min(xmin, xmax), max(xmin, xmax)
        ymin, ymax = min(ymin, ymax), max(ymin, ymax)
        if xmin < -180 or ymin < -90 or xmax > 180 or ymax > 90:
            raise ValueError('Out of bounds')
        return bbox

    @validator('records_per_page')
    def maximumRecordsValidation(cls, v):
        if v is None or v <= 100:
            return v
        raise ValueError('recordsPerPage maximum allowed value is 100')
