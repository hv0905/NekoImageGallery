import asyncio
import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import config

TEST_ACCESS_TOKEN = 'test_token'
TEST_ADMIN_TOKEN = 'test_admin_token'

assets_path = Path(__file__).parent / '..' / 'assets'


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


@pytest.fixture()
def check_local_dir_empty():
    yield
    dir = Path(config.config.storage.local.path)
    files = [f for f in dir.glob('*.*') if f.is_file()]
    assert len(files) == 0

    thumbnail_dir = dir / 'thumbnails'
    if thumbnail_dir.exists():
        thumbnail_files = [f for f in thumbnail_dir.glob('*.*') if f.is_file()]
        assert len(thumbnail_files) == 0


@pytest.fixture()
def wait_for_background_task(test_client):
    async def func(expected_image_count):
        while True:
            resp = test_client.get('/admin/server_info', headers={'x-admin-token': TEST_ADMIN_TOKEN})
            if resp.json()['image_count'] >= expected_image_count:
                break
            await asyncio.sleep(0.2)
        assert resp.json()['index_queue_length'] == 0

    return func


@pytest.fixture
def anyio_backend():
    return 'asyncio'
