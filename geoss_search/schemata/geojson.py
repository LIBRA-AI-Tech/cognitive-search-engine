from turtle import title
from fastapi import Query
from pydantic import BaseModel, Field
from typing import List, Literal, Union, Tuple
from typing_extensions import Annotated
from enum import Enum

class GeometryType(str, Enum):
    polygon: str = 'Polygon'
    point: str = 'Point'

class PolygonGeometry(BaseModel):
    """Polygon geometry"""
    type: Literal['Polygon'] = Query(..., description="Geometry type")
    coordinates: List[List[Tuple[float, float]]] = Field(..., description="Feature geometry")

class PointGeometry(BaseModel):
    """Point geometry"""
    type: Literal['Point'] = Query(..., description="Geometry type")
    coordinates: List[float] = Field(..., description="Feature geometry", min_items=2, max_items=2)

class FeatureProperties(BaseModel):
    groupId: str = Query(..., description='ID of the group that this feature belongs.')

class Feature(BaseModel):
    """Feature model"""
    type: Literal['Feature'] = Query(..., description="Type; always feature")
    id: str = Query(..., description="Record id")
    geometry: Union[PolygonGeometry, PointGeometry] = Query(None, description="Feature geometry")
    properties: FeatureProperties = Query(..., description="Feature additional properties")

class GeoJSON(BaseModel):
    """GeoJSON model"""
    type: Literal['FeatureCollection'] = Query(..., description="GeoJSON type; always FeatureCollection")
    features: List[Feature] = Query(..., description="List of features.")
