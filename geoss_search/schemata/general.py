import os
from fastapi import Query
from pydantic import BaseModel, Field, DirectoryPath, validator
from typing import List, Optional, Union, Any
from enum import Enum
from datetime import datetime
from .geojson import GeoJSON

class SpatialPredicate(str, Enum):
    """Spatial predicates"""
    overlaps: str = "overlaps"
    contains: str = "contains"
    disjoint: str = "disjoint"

class QueryMethod(str, Enum):
    """Possible query methods"""
    exact: str = "exact"
    semantic: str = "semantic"

class Online(BaseModel):
    """Online resource model"""
    protocol: str = Query(None, description="Resource protocol")
    function: str = Query(None, description="Resource purpose (e.g. download, info, etc).")
    name: str = Query(None, description="Resource name")
    description: str = Query(None, description="Resource description")
    url: str = Query(None, description="Resource URL")

class BBox(BaseModel):
    """Bounding Box model"""
    east: float = Query(..., description="East boundary")
    south: float = Query(..., description="South boundary")
    north: float = Query(..., description="North boundary")
    west: float = Query(..., description="North boundary")

class SearchGroup(BaseModel):
    """Individual matching group"""
    groupId: str = Query(..., title="Group id (uuid)", description="Group id. Multiple records belong to the same group when they have same values for title, description, and originator organisation.")
    memberCount: int = Query(..., title="Member count", description="Number of records in this group (satisfying the query criteria)")
    members: List[str] = Query(..., title="Members IDs", description="List of IDs of records belonging to this group and satisfying the search criteria.")
    title: str = Query(..., description="Common title of all records belonging to this group.")
    description: Optional[str] = Query(..., description="Common description of all records belonging to this group.")
    origOrgId: str = Query(..., description="Common dataset originator organisation ID of all records in this group.")
    origOrgDesc: str = Query(..., description="Common dataset originator organisation description of all records in this group.")
    score: float = Query(..., description="Cosine similarity score for the characteristics of this group.")

class SearchItem(BaseModel):
    """Individual matching record"""
    id: str = Query(..., description="Record id")
    title: str = Query(..., description="Record title")
    description: Optional[str] = Query(..., description="Record description")
    score: float = Query(..., description="Cosine similarity score of this record")
    origOrgDesc: str = Query(..., description="Dataset organisation")
    online: List[Online] = Query(..., description="List of online resources")
    where: List[BBox] = Query(..., description="List of Bounding boxes for the corresponding dataset(s)")

class SignificantTerms(BaseModel):
    """Significant terms model"""
    term: str = Query(..., description="Significant term")
    freq: int = Query(..., title="Frequency", description="Frequency of the term in the query results")
    bgFreq: int = Query(None, title="Background frequency", description="Background frequency of the term; only when results are sorted by significance")
    score: float = Query(None, description="Significance score; only when results are sorted by significance")

class SignificantSources(SignificantTerms):
    """Significant terms for source attribute model"""
    termId: str = Query(..., description="Source id")

class SignificantTermsList(BaseModel):
    """List of attributes for which significant terms are computed"""
    keyword: List[SignificantTerms] = Query(..., description="Significant keywords, sorted by significance score")
    format: List[SignificantTerms] = Query(..., description="Significant formats, sorted by significance score")
    source: List[SignificantSources] = Query(..., description="Significant sources, sorted by significance score")
    protocol: List[SignificantTerms] = Query(..., description="Significant protocols, sorted by significance score")
    organisation: List[SignificantTerms] = Query(..., description="Significant organisations, sorted by significance score")
    ontology: List[SignificantTerms] = Query(..., description="Significant ontologies, sorted by significance score")
    concept: List[SignificantTerms] = Query(..., description="Significant ontology concepts, sorted by significance score")
    individual: List[SignificantTerms] = Query(..., description="Significant ontology individuals, sorted by significance score")
    extractedKeyword: List[SignificantTerms] = Query(..., description="Significant extracted keywords, sorted by significance score")
    extractedFiletype: List[SignificantTerms] = Query(..., description="Significant extracted file types, sorted by significance score")

class SearchResults(BaseModel):
    """Output of search query."""
    
    page: int = Query(..., description="Current page")
    totalPages: int = Query(..., description="Total number of pages")
    numberOfResults: int = Query(..., description="Total number of results")
    data: List[SearchGroup] = Query(..., description="Matching records.")
    significantTerms: SignificantTermsList = Query(..., description="Significant Terms for keyword, format, source, protocol, and organisation attributes according to the the specific query.")
    geoJson: GeoJSON = Query(..., description="GeoJSON representing current page geometries")

    class Config:
        schema_extra = {
            "example": {
                "page": 1,
                "totalPages":102,
                "numberOfResults": 512,
                "data": [
                    {
                        "groupId": "be8435c2-64b1-4c7a-b40c-5f870ce40ffe",
                        "memberCount": 17,
                        "members": ['c6d4e13e-fc77-4318-8dd3-ff39926f659a', '8f32527e-7f20-4912-9097-f90fc98a8758', '67a6c8bc-3bbc-4765-ab7c-34edebb35b3a', '0ebdd08c-0225-4fb5-9138-647110e14708', '21c3e90b-716f-4762-9307-1615cc3f86af', 'fe69f21b-3f19-4219-9c2c-b6d7ce13ff76', '3527c1d3-7d5f-4038-a3f0-6e5a50f3abc8', '17089cb3-3b72-48cb-bd06-a9f286a9aff1', '9cac5166-20c3-4829-8b93-6f7f88573cdc', 'ebe2d233-94d6-41d5-97b3-17ed4173f012', '1c8cf20d-d8c4-470f-a0f3-9f6e9fab5059', '257cba4c-0e01-4a3b-a4c5-01511a0cf2d9', '929a5009-7d74-4db7-abab-4a8d4f937a34', 'b081f097-1c53-4336-aeea-5078a436f9ff', '5b793c79-aa32-45dc-a0f5-ebf06df813d5', '8d9b8146-b361-48af-bb47-817b77ae793a', '41a6c575-9064-45f4-adb6-9b9ab2166805'],
                        "title": "Dissolved trace metals concentrations obtained during R/V Hakuho-maru KH-14-3 cruise",
                        "description": "Dissolved trace metals concentrations obtained during R/V Hakuho-maru KH-14-3 cruise",
                        "origOrgId": "adsdbid",
                        "origOrgDesc": "Arctic Data archive System",
                        "score": 0.78
                    }
                ],
                "significantTerms": {
                    "keyword": [
                        {
                            "term": "Oceanographic geographical features",
                            "freq": 821,
                            "bgFreq": 1346,
                            "score": 4.247498051976547
                        },
                        {
                            "term": "marine-safety",
                            "freq": 331,
                            "bgFreq": 416,
                            "score": 2.2899052958360606
                        },
                        {
                            "term": "weather-climate-and-seasonal-forecasting",
                            "freq": 325,
                            "bgFreq": 410,
                            "score": 2.2392676495804094
                        }
                    ],
                    "format": [
                        {
                            "term": "Ocean Data View ASCII input",
                            "freq": 328,
                            "bgFreq": 515,
                            "score": 1.7799287193084226
                        },
                        {
                            "term": "Climate and Forecast Point Data NetCDF",
                            "freq": 240,
                            "bgFreq": 427,
                            "score": 1.1336782636042086
                        },
                        {
                            "term": "NetCDF-4",
                            "freq": 165,
                            "bgFreq": 217,
                            "score": 1.0867731140044627
                        }
                    ],
                    "source": [
                        {
                            "term": "SeaDataNet - Open datasets",
                            "freq": 200,
                            "bgFreq": 200,
                            "score": 1.767505855597803,
                            "termId": "seadatanet-open"
                        },
                        {
                            "term": "World Ocean Database",
                            "freq": 200,
                            "bgFreq": 200,
                            "score": 1.767505855597803,
                            "termId": "wod"
                        },
                        {
                            "term": "SeaDataNet",
                            "freq": 200,
                            "bgFreq": 200,
                            "score": 1.767505855597803,
                            "termId": "UUID-e8f7704a-bcd1-42c4-853c-bbb9a6caadce"
                        }
                    ],
                    "protocol": [
                        {
                            "term": "WWW:FTP",
                            "freq": 171,
                            "bgFreq": 229,
                            "score": 1.1043758278839244
                        },
                        {
                            "term": "MYO:MOTU-SUB",
                            "freq": 100,
                            "bgFreq": 136,
                            "score": 0.6350960888660704
                        },
                        {
                            "term": "OGC:WMS:getCapabilities",
                            "freq": 103,
                            "bgFreq": 146,
                            "score": 0.6253017504308953
                        }
                    ],
                    "organisation": [
                        {
                            "term": "National Centers for Environmental Information (NCEI), NOAA",
                            "freq": 198,
                            "bgFreq": 198,
                            "score": 1.749830797041825
                        },
                        {
                            "term": "servicedesk.cmems@mercator-ocean.eu",
                            "freq": 141,
                            "bgFreq": 166,
                            "score": 1.0466169150364792
                        },
                        {
                            "term": "OC-CNR-ROMA-IT",
                            "freq": 45,
                            "bgFreq": 47,
                            "score": 0.37970087596968394
                        }
                    ],
                    "ontology": [
                        {
                            "term": "sdg",
                            "freq": 198,
                            "bgFreq": 198,
                            "score": 1.749830797041825
                        },
                        {
                            "term": "eo",
                            "freq": 141,
                            "bgFreq": 166,
                            "score": 1.0466169150364792
                        },
                        {
                            "term": "ecv",
                            "freq": 45,
                            "bgFreq": 47,
                            "score": 0.37970087596968394
                        }
                    ],
                    "concept": [
                        {
                            "term": "goal",
                            "freq": 23,
                            "bgFreq": 52,
                            "score": 1.00222
                        }
                    ],
                    "individual": [
                        {
                            "term": "http://metadata.un.org/sdg/1.1",
                            "freq": 198,
                            "bgFreq": 198,
                            "score": 1.749830797041825
                        },
                        {
                            "term": "http://metadata.un.org/sdg/1.3",
                            "freq": 141,
                            "bgFreq": 166,
                            "score": 1.0466169150364792
                        }
                    ],
                    "extractedKeyword": [
                        {
                            "term": "climate change",
                            "freq": 198,
                            "bgFreq": 198,
                            "score": 1.749830797041825
                        },
                        {
                            "term": "green house gases",
                            "freq": 141,
                            "bgFreq": 166,
                            "score": 1.0466169150364792
                        }
                    ],
                    "extractedFiletype": [
                        {
                            "term": "pdf",
                            "freq": 198,
                            "bgFreq": 198,
                            "score": 1.749830797041825
                        },
                        {
                            "term": "csv",
                            "freq": 141,
                            "bgFreq": 166,
                            "score": 1.0466169150364792
                        }
                    ]
                },
                "geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "id": "f399fad7-b8fb-49de-8ba1-452c58c30716",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [10.2, 48.1]
                            },
                            "properties": {
                                "groupId": "be8435c2-64b1-4c7a-b40c-5f870ce40ffe"
                            }
                        },
                        {
                            "type": "Feature",
                            "id": "310a772a-f7e9-48a9-a7a0-dc9dd614b356",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [[[5.3, 50.1], [15.1, 50.1], [15.1, 40.2], [5.3, 40.2], [5.3, 50.1]]]
                            },
                            "properties": {
                                "groupId": "be8435c2-64b1-4c7a-b40c-5f870ce40ffe"
                            }
                        }
                    ]
                }
                # "data": [{
                #     "id": "06211824-2453-488a-acfa-f97c63b7f17b",
                #     "title": "First Ice Camp of east of the Northern Northwind Ridge site at 50km northweat from Araon in by 2014 Araon Cruse.",
                #     "description": "First ice camp observation datasets of east of the Northern Northwind Ridge site at 50km northweat from Araon in by 2014 Araon Cruse. This dataset included to SBE37, SBE56, DEFI and WH600.",
                #     "score": 1.02,
                #     "origOrgDesc": "NO01L, Norwegian Institute for Air Research, NILU, Instituttveien 18, 2007, Kjeller, Norway",
                #     "online": [
                #         {
                #             "protocol": "urn:ogc:serviceType:WaterOneFlow:1.1:HTTP",
                #             "function": "download",
                #             "name": "method;0;parameter;hsl-emr:Tmin;platform;hsl-emr:VOLANOAGRO;quality;1;source;1",
                #             "url": "http://hydroserver.ddns.net/italia/hsl-emr/index.php/default/services/cuahsi_1_1.asmx?WSDL"
                #         }, {
                #             "protocol": "GWIS",
                #             "function": "mapDigital",
                #             "description": "This URL provides an NCDC climate and weather toolkit view of an OPeNDAP resource.",
                #             "url": "http://gs-service-production.geodab.eu/gs-service/services/essi/view/geoss/gwis?request=plot&onlineId=urn:uuid:adafc208-5572-46a4-a810-3b5c1876e6c4"
                #         }
                #     ],
                #     "where": [{
                #         "east": 12.24903,
                #         "south": 44.81408,
                #         "north": 44.81408,
                #         "west": 12.24903
                #     }]
                # }]
            }
        }

class SourceSchema(BaseModel):
    """Source Model"""
    id: str = Query(..., description="Source identifier")
    title: str = Query(..., description="Source title")

    class Config:
        schema_extra = {
            "example": {
                "id": "adsdbid",
                "title": "Arctic Data archive System"
            }
        }

class TimePeriod(BaseModel):
    """Time period model"""
    from_: Union[datetime, Any] = Query(None, description="Begin of temporal extent")
    to: Union[datetime, Any] = Query(None, description="End of temporal extent")

    class Config:
        fields = {
            'from_': 'from',
        }

class AuthorModel(BaseModel):
    """Author model"""
    city: Optional[str] = Query(..., description="Affiliation City")
    email: Optional[str] = Query(..., description="Author email")
    individualName: Optional[str] = Query(..., description="Author full name")
    online: Optional[List[Online]] = Query(..., description="Online resources")
    orgName: Optional[str] = Query(..., description="Organisation name")
    posName: Optional[str] = Query(..., description="Position title")

class VerticalExtentModel(BaseModel):
    """Vertical extent mode"""
    max: float = Query(..., description="Upper bound of vertical extent")
    min: float = Query(..., description="Lower bound of vertical extent")

class RawMetadata(BaseModel):
    """Raw metadata model"""
    format: List[str] = Query(None, description="Actual data format(s)")
    description: str = Query(None, description="Dataset description")
    attributeDescription: List[str] = Query(None, description="Description of attributes")
    source: SourceSchema = Query(None, description="Originator source")
    attributeTitle: List[str] = Query(None, description="Attributes' titles")
    type: str = Query(None, description="Dataset type")
    title: str = Query(..., description="Dataset title")
    when: List[TimePeriod] = Query(None, description="List of dataset's temporal extent")
    rights: List[str] = Query(None, description="List of rights for the dataset")
    platformDescription: List[str] = Query(None, description="Platform description")
    platformTitle: List[str] = Query(None, description="Platform title")
    online: List[Online] = Query(None, description="Description with associated online resources")
    where: List[BBox] = Query(None, description="List of dataset's spatial extent")
    id: str = Query(..., description="Dataset's identifier")
    keyword: List[str] = Query(None, description="List of available keywords")
    coverageDescription: str = Query(None, description="Coverage description")
    origOrgDesc: List[str] = Query(None, description="Description of originators organizations")
    created: str = Query(None, description="Created time (string; not always in ISO format)")
    update: str = Query(None, description="Update time (string; not always in ISO format)")
    topic: List[str] = Query(None, description="List of free text topics describing the dataset")
    geossCategory: List[str] = Query(None, description="GEOSS category associated to the dataset")
    verticalExtent: List[VerticalExtentModel] = Query(None, description="Vertical extent (if applicable)")
    spatialRepresentationType: str = Query(None, description="Spatial representation type (free text)")
    parentId: str = Query(None, description="Parent id")
    overview: List[str] = Query(None, description="List of dataset's overview (free text)")
    alternateTitle: str = Query(None, description="Alternate title")
    author: List[AuthorModel] = Query(None, description="Dataset's Author")

    class Config:
        schema_extra = {
            "example": {
                "format": [
                    "WaterML 1.1"
                ],
                "attributeDescription": [
                    "Water Level Data type: Unknown Value type: Field Observation Units: meter Units type: Length Unit abbreviation: m No data value: -9999 Speciation: Not Applicable"
                ],
                "source": {
                    "id": "UUID-a4002f3f-862b-411c-b617-71349b711742",
                    "title": "Italy, Italian Institute for Environmental Protection and Research (ISPRA) - Monitoring Network"
                },
                "attributeTitle": [
                    "Water Level"
                ],
                "type": "simple",
                "title": "PIACENZA - Water Level - Unknown",
                "when": [
                    {
                        "from": "1991-01-01T11:00:00Z",
                        "to": "2020-12-31T11:00:00Z"
                    }
                ],
                "platformDescription": [
                    "PIACENZA"
                ],
                "platformTitle": [
                    "PIACENZA"
                ],
                "online": [
                    {
                        "protocol": "urn:ogc:serviceType:WaterOneFlow:1.1:HTTP",
                        "function": "download",
                        "name": "method;0;parameter;hsl-emr:Water_Level;platform;hsl-emr:PIACENZA;quality;1;source;1",
                        "url": "http://hydroserver.ddns.net/italia/hsl-emr/index.php/default/services/cuahsi_1_1.asmx?WSDL"
                    },
                    {
                        "protocol": "GWIS",
                        "function": "info",
                        "url": "http://gs-service-production.geodab.eu/gs-service/services/essi/view/geoss/gwis?request=plot&onlineId=urn:uuid:b3cc5b16-fbd8-4885-8bf5-2f75db1f83e4"
                    }
                ],
                "where": [
                    {
                        "east": 9.7053,
                        "south": 45.0633,
                        "north": 45.0633,
                        "west": 9.7053
                    }
                ],
                "id": "a2dd6ef3-00cc-436a-87bd-8f5fff729f6c",
                "keyword": [
                    "RER",
                    "Hydrology",
                    "Surface Water",
                    "meter",
                    "Length",
                    "Quality controlled data",
                    "Field Observation",
                    "Unknown"
                ],
                "coverageDescription": "Water Level Data type: Unknown Value type: Field Observation Units: meter Units type: Length Unit abbreviation: m No data value: -9999 Speciation: Not Applicable",
                "origOrgDesc": [
                    "ISPRA, Italian Environment Protection and Technical Services Agency - Monitoring Network"
                ]
            }
        }

class ListOfRecords(BaseModel):
    """List of records model"""
    total: int = Field(..., description="Number of records in the response", example=1)
    bbox: List[float] = Field(..., description="Bounding box of the records in the form [lon_min, lat_min, lon_max, lat_max]", min_items=4, max_items=4, example=[-11.5,35.3,43.2,81.4])
    records: List[RawMetadata] = Field(..., description="List of records")

class Attributes(str, Enum):
    """Available attributes"""
    format: str='format'
    description: str='description'
    attributeDescription: str='attributeDescription'
    source: str='source'
    attributeTitle: str='attributeTitle'
    type: str='type'
    title: str='title'
    when: str='when'
    rights: str='rights'
    platformDescription: str='platformDescription'
    platformTitle: str='platformTitle'
    online: str='online'
    where: str='where'
    id: str='id'
    keyword: str='keyword'
    coverageDescription: str='coverageDescription'
    origOrgDesc: str='origOrgDesc'
    created: str='created'
    update: str='update'
    topic: str='topic'
    geossCategory: str='geossCategory'
    verticalExtent: str='verticalExtent'
    spatialRepresentationType: str='spatialRepresentationType'
    parentId: str='parentId'
    overview: str='overview'
    alternateTitle: str='alternateTitle'
    author: str='author'

class HealthStatus(str, Enum):
    """Possible health status values"""
    ok: str='OK'
    failed: str='FAILED'

class HealthResults(BaseModel):
    """Output of health endpoint"""
    status: HealthStatus = Query(..., description="Health status")
    details: str = Query(..., description="Details of problem in case of failure")
    message: str = Query(..., description="Additional message")

    class Config:
        use_enum_values = True

class IngestBody(BaseModel):
    """Ingest POST request body"""
    path: str = Field(..., description="Relative path of directory that contains the data files to ingest")
    elastic_index: str = Field(None, alias="elasticIndex", description="Name of the elastic index to ingest data; if exists only new files will inserted")
    embeddings: str = Field('embeddings', description="Name of the attribute that holds the embedding compoments")

    @validator('path')
    def build_abs_path(cls, value):
        path = os.path.join(os.getenv("INIT_DATA"), value)
        if not os.path.isdir(path):
            raise ValueError(f'Path `{value}` does not exist')
        return path
