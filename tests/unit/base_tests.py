from geoss_search.settings import settings
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
client = TestClient(app)

def setup_module():
    print(" == Setting up tests for %s"  % (__name__))
    print(" == Using elastic search at %s"  % (settings.elastic_node))

def teardown_module():
    print(" == Tearing down tests for %s"  % (__name__))

# Tests
def test_get_documentation_1():
    """Test OpenAPI documentation"""
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert r.json().get('openapi') is not None
