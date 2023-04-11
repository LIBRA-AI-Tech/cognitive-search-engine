import os
from typing import Optional, List
from geoss_search.elastic import engine_connect
from fastapi import Security, status
from fastapi.exceptions import HTTPException
from fastapi.security.api_key import APIKeyHeader

es = engine_connect()

api_key_header = APIKeyHeader(name="api-key", auto_error=False)

def admin_key_auth(api_key: str=Security(api_key_header)):
    _authenticate(keys=[os.getenv('ADMIN_KEY')], api_key=api_key)

def api_key_auth(api_key: str=Security(api_key_header)):
    _authenticate(api_key=api_key)

def _authenticate(keys: Optional[List[str]]=None, api_key: str=Security(api_key_header)):
    if keys is None:
        keys = [os.getenv('ADMIN_KEY'), os.getenv('API_KEY')]
    if api_key is None or api_key not in keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )
