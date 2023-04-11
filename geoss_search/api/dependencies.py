import os
from geoss_search.elastic import engine_connect
from fastapi import Security, status
from fastapi.exceptions import HTTPException
from fastapi.security.api_key import APIKeyHeader

es = engine_connect()

api_key_header = APIKeyHeader(name="api-key", auto_error=False)
def api_key_auth(api_key: str=Security(api_key_header)):
    if api_key != os.getenv('API_KEY'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden"
        )
