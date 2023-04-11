from fastapi import Query
from pydantic import BaseModel, Field
from datetime import datetime

class NewOntology(BaseModel):
    """New Ontology Schema"""
    record_id: str = Field(..., alias="recordId", description="Unique ID of GEOSS metadata")
    ontology: str = Field(..., description="EIFF-O ontology name")
    concept: str = Field(..., description="EIFF-O ontology concept")
    individual: str = Field(..., description="EIFF-O individual")
    description: str = Field(..., description="EIFF-O individual description")

    class Config:
        schema_extra = {
            "example": {
                "record_id": "d1eee9f7-67a5-4cbb-a2ee-d6b5645201ab",
                "ontology": "sdg",
                "concept": "goal",
                "individual": "http://metadata.un.org/sdg/1",
                "description": "End poverty in all its forms everywhere"
            }
        }

class UpdateOntology(BaseModel):
    """Update Ontology Schema"""
    ontology: str = Field(None, description="EIFF-O ontology")
    concept: str = Field(None, description="EIFF-O ontology concept")
    individual: str = Field(None, description="EIFF-O individual")
    description: str = Field(None, description="EIFF-O individual description")

class SingleOntologyResponse(BaseModel):
    """Single Ontology Response"""
    id: str = Field(..., description="Unique ID of ontology record")
    ontology: str = Field(..., description="EIFF-O ontology")
    concept: str = Field(..., description="EIFF-O ontology concept")
    individual: str = Field(..., description="EIFF-O individual")
    description: str = Field(..., description="EIFF-O individual description")
    creation: datetime = Field(..., description="Creation datetime of the ontology record")

    class Config:
        schema_extra = {
            "example": {
                "id": "RQ47cIcBvFIE6aq5sCoO",
                "ontology": "sdg",
                "concept": "goal",
                "individual": "http://metadata.un.org/sdg/1",
                "description": "End poverty in all its forms everywhere",
                "creation": "2023-04-11T12:12:52.601521"
            }
        }
