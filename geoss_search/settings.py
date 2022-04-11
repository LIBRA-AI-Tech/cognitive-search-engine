from pydantic import BaseSettings

class Settings(BaseSettings):
    """Settings variables

    Settings read from environment variables (characters are capitalized)
    """
    app_name: str = 'geoss_search'
    fastapi_env: str = 'development'
    elastic_node: str
    ca_certs: str = None
    elastic_password: str = None
    model_path: str
    quantize_model: bool
    elastic_index: str
    results_per_page: int = 5

settings = Settings()
