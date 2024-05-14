import importlib

import pytest
from fastapi.testclient import TestClient

from app import config

TEST_ACCESS_TOKEN = 'test_token'
TEST_ADMIN_TOKEN = 'test_admin_token'


@pytest.fixture(scope="session")
def test_client(tmp_path_factory) -> TestClient:
    # Modify the configuration for testing
    config.config.qdrant.mode = "memory"
    config.config.admin_api_enable = True
    config.config.access_protected = True
    config.config.access_token = TEST_ACCESS_TOKEN
    config.config.admin_token = TEST_ADMIN_TOKEN
    config.config.storage.method = config.StorageMode.LOCAL
    config.config.storage.local.path = tmp_path_factory.mktemp("static_files")
    # Start the application

    with TestClient(importlib.import_module('app.webapp').app) as client:
        yield client


@pytest.fixture
def anyio_backend():
    return 'asyncio'
