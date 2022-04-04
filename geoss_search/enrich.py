from typing import Union
from .model_inference import predict

def _toWKT(coords: dict) -> dict:
    return  "POINT({west} {south})".format(**coords) \
        if coords['west'] == coords['east'] and coords['north'] == coords['south'] \
        else "BBOX({west}, {east}, {north}, {south})".format(**coords)

def enrich(entry: Union[dict, list]) -> Union[dict, list]:
    if isinstance(entry, list):
        return [enrich(element) for element in entry]
    entry['_embedding'] = predict(entry['description'])
    entry['_geom'] = [_toWKT(elem) for elem in entry['where']]
    return entry
