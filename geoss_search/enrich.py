from typing import Union
from .model_inference import predict

def _toWKT(coords: dict) -> dict:
    """Transforms to WKT format

    Transforms coordinates to bounding box WKT.

    Args:
        coords (dict): A dictionary of coordinates given by the keys `north`, `east`, `south`, `west`

    Returns:
        dict: The WKT string for the bounding box.
    """
    return  "POINT({west} {south})".format(**coords) \
        if coords['west'] == coords['east'] and coords['north'] == coords['south'] \
        else "BBOX({west}, {east}, {north}, {south})".format(**coords)

def enrich(entry: Union[dict, list]) -> Union[dict, list]:
    """Enrich an entry or list of entries

    Args:
        entry (Union[dict, list]): An entry dictionary, or list of entries

    Returns:
        Union[dict, list]: The enriched entry or entries.
    """
    if isinstance(entry, list):
        return [enrich(element) for element in entry]
    entry['_embedding'] = predict(entry['description'])
    entry['_geom'] = [_toWKT(elem) for elem in entry['where']]
    return entry
