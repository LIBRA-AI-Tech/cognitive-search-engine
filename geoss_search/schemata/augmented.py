from pydantic import BaseModel, Field
from typing import Dict, List

class Insights(BaseModel):
    title: str = Field(None, description="Title of the dataset as extracted from WMS/WFS")
    description: str = Field(None, description="Description of the dataset as extracted from WMS/WFS")
    keywords: str = Field(None, description="Additional keywords provided from the service / layers")
    driver: str = Field(None, description="Driver / data type of the specific data source")
    numberOfFiles: str = Field(None, description="Number of included data files")
    totalFeatures: str = Field(None, description="Total number of features (records)")
    numberOfAttributes: str = Field(None, description="Total number of attributes (fields)")
    convexHull: str = Field(None, description="Convex hull or MBR from individual bounding boxes or geometries, given in WKT format")
    attributes: str = Field(None, description="Layers or attributes names (first 5)")
    datasetMetadata: str = Field(None, description="Dataset specific metadata")
    dimensions: str = Field(None, description="Number of dimensions in multi-dimensional sources")
    variableSize: str = Field(None, description="Number of variables in multi-dimensional sources")
    temporalExtent: str = Field(None, description="Temporal extent (including time unit)")
    timeResolution: str = Field(None, description="Resolution in time (same units as temporalExtent")

class CategoricalSchema(BaseModel):
    code: str = Field(None, description="NUTS code")
    label: str = Field(None, description="NUTS latin name")
    coverage: float = Field(None, description="Percentage of this NUTS covered by the dataset area")

class NutsLevels(BaseModel):
    nuts0: List[CategoricalSchema] = Field(None, alias="NUTS0", description="NUTS level 0 coverage")
    nuts1: List[CategoricalSchema] = Field(None, alias="NUTS1", description="NUTS level 1 coverage")
    nuts2: List[CategoricalSchema] = Field(None, alias="NUTS2", description="NUTS level 2 coverage")
    nuts3: List[CategoricalSchema] = Field(None, alias="NUTS3", description="NUTS level 3 coverage")

class Statistics(BaseModel):
    avg: float = Field(None, description="Average value")
    min: float = Field(None, description="Minimum value")
    max: float = Field(None, description="Maximum value")
    stddev: float = Field(None, description="Standard deviation")

class AirQuality(BaseModel):
    o3_aot40v: Statistics = Field(None, alias="O3_AOT40v", description="Ozone AOT40 values for Vegetation")
    o3_aot40f: Statistics = Field(None, alias="O3_AOT40f", description="Ozone AOT40 values for Forests")
    nox_avg: Statistics = Field(None, alias="NOx_avg", description="NOx annual average")
    dif_aot40v: Statistics = Field(None, alias="dif_AOT40v", description="Interannual difference in Ozone AOT40 values for Vegetation")
    dif_aot40f: Statistics = Field(None, alias="dif_AOT40f", description="Interannual difference in Ozone AOT40 values for Forests")
    dif_noxavg: Statistics = Field(None, alias="dif_NOxavg", description="Interannual difference in NOx annual average values for 2018-17")
    pod6_wheat: Statistics = Field(None, alias="POD6_wheat", description="Phytoxic Ozone Dose for wheat")
    pod6potato: Statistics = Field(None, alias="POD6potato", description="Phytoxic Ozone Dose for potato")
    pod6tomato: Statistics = Field(None, alias="POD6tomato", description="Phytoxic Ozone Dose for tomato")
    coverage: float = Field(None, description="Coverage percentage of the area within the air quality dataset")

class ExternalSources(BaseModel):
    nuts: NutsLevels = Field(None, alias="NUTS", description="NUTS coverage for each level")
    soil: str = Field(None, alias="Soil", description="Soil erosion")
    land_use: List[CategoricalSchema] = Field(None, alias="landUse", description="Corine land use coverage")
    air_quality: AirQuality = Field(None, alias="airQuality", description="Air quality data")
    population: int = Field(None, description="Estimation of total population of the selected area based on NUTS3 population density")
    soil_erosion: float = Field(None, alias="soilErosion", description="Soil erosion in tonnes per hectare")
    heating_degree_days: float = Field(None, alias="heatingDegreeDays", description="Heating degree days")
    cooling_degree_days: float = Field(None, alias="coolingDegreeDays", description="Cooling degree days")

class Augmented(BaseModel):
    insights: Insights = Field(None, description="Metadata from data insights")
    external_sources: ExternalSources = Field(None, alias="externalSources", description="Metadata extracted from external sources")
    extracted_keyphrases: str = Field(None, alias="extractedKeyphrases", description="Extracted keyphrases from original metadata")

# class Augmented(BaseModel):
#     landUse: str = Field(None, description="Dominant land uses; using Corine dataset")
#     AQ_O3_AOT40v: str = Field(None, description="Ozone AOT40 values for Vegetation")
#     AQ_O3_AOT40f: str = Field(None, description="Ozone AOT40 values for Forests")
#     AQ_NOx_avg: str = Field(None, description="NOx annual average")
#     AQ_dif_AOT40v: str = Field(None, description="Interannual difference in Ozone AOT40 values for Vegetation")
#     AQ_dif_AOT40f: str = Field(None, description="Interannual difference in Ozone AOT40 values for Forests")
#     AQ_dif_NOxavg: str = Field(None, description="Interannual difference in NOx annual average values for 2018-17")
#     AQ_POD6_wheat: str = Field(None, description="Phytoxic Ozone Dose for wheat")
#     AQ_POD6potato: str = Field(None, description="Phytoxic Ozone Dose for potato")
#     AQ_POD6tomato: str = Field(None, description="Phytoxic Ozone Dose for tomato")
#     NUTS_0_ID: str = Field(None, description="NUTS-0 id")
#     NUTS_0_NAME: str = Field(None, description="NUTS-0 name")
#     NUTS_1_ID: str = Field(None, description="NUTS-1 id")
#     NUTS_1_NAME: str = Field(None, description="NUTS-2 name")
#     NUTS_2_ID: str = Field(None, description="NUTS-2 id")
#     NUTS_2_NAME: str = Field(None, description="NUTS-3 name")
#     NUTS_3_ID: str = Field(None, description="NUTS-3 id")
#     NUTS_3_NAME: str = Field(None, description="NUTS-3 name")
#     populationDensity: str = Field(None, description="Population density (2019)")
#     soilErosion: str = Field(None, description="Soil Erosion")
#     coolingDegreeDays: str = Field(None, description="Cooling degrees days (annual)")
#     heatingDegreeDays: str = Field(None, description="Heating degrees days (annual)")
#     extractedKeyphrases: str = Field(None, description="Extracted keyphrases using NLP")
