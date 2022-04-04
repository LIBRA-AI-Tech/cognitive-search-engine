from fastapi import Query
from pydantic import BaseModel
from typing import List

class SearchItem(BaseModel):
    """Individual matching record."""
    id: str = Query(..., description="Record id")
    title: str = Query(..., description="Record title")
    description: str = Query(..., description="Record description")
    score: float = Query(..., description="Cosine similarity score of this record")

class SearchResults(BaseModel):
    """Output of search query."""
    
    page: int = Query(..., description="Current page")
    totalPages: int = Query(..., description="Total number of pages")
    numberOfResults: int = Query(..., description="Total number of results")
    maxScore: float = Query(..., description="Maximum value of scores")
    data: List[SearchItem] = Query(..., description="Matching records.")

    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "totalPages":102,
                "numberOfResults": 512,
                "maxScore": 1.12,
                "data": [{
                    "id": "06211824-2453-488a-acfa-f97c63b7f17b",
                    "title": "First Ice Camp of east of the Northern Northwind Ridge site at 50km northweat from Araon in by 2014 Araon Cruse.",
                    "description": "First ice camp observation datasets of east of the Northern Northwind Ridge site at 50km northweat from Araon in by 2014 Araon Cruse. This dataset included to SBE37, SBE56, DEFI and WH600.",
                    "score": 1.02
                }]
            }
        }
