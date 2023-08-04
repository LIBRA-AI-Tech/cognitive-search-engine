from fastapi import Query
from typing import List, Optional
from pydantic import BaseModel, Field

class SemanticSingleResult(BaseModel):
    """id / score pair"""
    id: str = Field(..., description="Record ID", example="e000bd08-ef7a-48ce-b1b0-ea709ac7592d")
    score: float = Field(..., description="Similarity (cosine) score", example=0.76932776, le=1.0, ge=0.0)

class SemanticFilterResponse(BaseModel):
    """Response schema for semantic filtering query"""
    size: int = Field(..., description="Size of results with cosine similarity above the threshold.", example=919, ge=0, le=10000)
    max_score: Optional[float] = Field(..., alias="maxScore", description="Maximum value of cosine similarity.", example=0.76932776, le=1.0, ge=0.0)
    results: List[Optional[SemanticSingleResult]] = Field(..., description="List of record IDs sorted by descending similarity score.")

class SemanticSortBody(BaseModel):
    """Request body for semantic sorting"""
    ids: List[str] = Query(..., description="List of record IDs")
    query: str = Query(..., description="Semantic query that will be used to sort the record IDs", example="Inland water pollution")

class SemanticSortResponse(BaseModel):
    query: str = Field(..., description="Query on which the sort is based")
    sorted: List[Optional[SemanticSingleResult]] = Field(..., description="List of record IDs sorted by descending similarity score.")
