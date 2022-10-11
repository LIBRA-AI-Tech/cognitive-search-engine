import logging
from typing import Union
import pandas as pd
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
            else "POLYGON(({west} {north}, {east} {north}, {east} {south}, {west} {south}, {west} {north}))".format(**coords)

def enrich(entry: Union[dict, list]) -> Union[dict, list]:
    """Enrich an entry or list of entries

    Args:
        entry (Union[dict, list]): An entry dictionary, or list of entries

    Returns:
        Union[dict, list]: The enriched entry or entries.
    """
    if isinstance(entry, list):
        return [enrich(element) for element in entry]
    if '_embedding' not in entry:
        text = entry['title'] + ' ' + entry['description'] if entry['description'] is not None else entry['title']
        entry['_embedding'] = predict(text)
    entry['_geom'] = [_toWKT(elem) for elem in entry['where']]
    return entry

def bulk_predict(df: pd.DataFrame, embeddings: str=None) -> pd.DataFrame:
    if embeddings is not None:
        df.rename({embeddings: '_embedding'}, axis=1, inplace=True)
    else:
        text = df.apply(lambda e: e['title'] + ' ' + e['description'] if e['description'] is not None else e['title'], axis=1).values
        df['_embedding'] = predict(text)
    df['_geom'] = df['where'].apply(lambda where: [_toWKT(e) for e in where] if where is not None else [])
    return df

def group_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    from uuid import uuid4
    def find_group(e):
        return gdf[(gdf['title']==e.title) & (gdf['description']==e.description) & (gdf['org']==e.org)].reset_index()['group']
    df.description.fillna('', inplace=True)
    df['org'] = df.source.apply(lambda e: e['id'])
    gdf = df.groupby(by=['title', 'description', 'org'], axis=0).apply(lambda e: str(uuid4())).to_frame(name="group")
    gdf.reset_index(inplace=True)
    df['_group'] = df.apply(find_group, axis=1)
    df.drop(labels='org', axis=1, inplace=True)
    return df
