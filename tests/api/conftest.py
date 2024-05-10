import pytest
from fastapi.testclient import TestClient

from app import config

TEST_ACCESS_TOKEN = 'test_token'
TEST_ADMIN_TOKEN = 'test_admin_token'

config.config.qdrant.mode = "memory"
config.config.admin_api_enable = True
config.config.access_protected = True
config.config.access_token = TEST_ACCESS_TOKEN
config.config.admin_token = TEST_ADMIN_TOKEN
config.config.storage.method = config.StorageMode.LOCAL


@pytest.fixture(scope="session")
def test_client(tmp_path_factory) -> TestClient:
    # Modify the configuration for testing
    config.config.storage.local.path = tmp_path_factory.mktemp("static_files")

    from app.webapp import app
    # Start the application

    with TestClient(app) as client:
        yield client
