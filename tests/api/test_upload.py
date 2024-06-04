import io
import random

import pytest

from .conftest import TEST_ADMIN_TOKEN, TEST_ACCESS_TOKEN


def test_upload_bad_img_file(test_client):
    bad_img_file = io.BytesIO(bytearray(random.getrandbits(8) for _ in range(1024 * 1024)))
    bad_img_file.name = 'bad_image.jpg'

    resp = test_client.post('/admin/upload',
                            files={'image_file': bad_img_file},
                            headers={'x-admin-token': TEST_ADMIN_TOKEN},
                            params={'local': True})
    assert resp.status_code == 422


def test_upload_unsupported_types(test_client):
    bad_img_file = io.BytesIO(bytearray(random.getrandbits(8) for _ in range(1024 * 1024)))
    bad_img_file.name = 'bad_image.tga'

    resp = test_client.post('/admin/upload',
                            files={'image_file': ('bad_img.tga', bad_img_file, 'image/tga')},
                            headers={'x-admin-token': TEST_ADMIN_TOKEN},
                            params={'local': True})
    assert resp.status_code == 415


TEST_FAKE_URL = 'fake-url'
TEST_FAKE_THUMBNAIL_URL = 'fake-thumbnail-url'

TEST_PARAMS = [
    (True, {'local': True}, True, 'local'),
    (True, {'local': True, 'local_thumbnail': 'never'}, True, 'none'),
    (False, {'local': True, 'local_thumbnail': 'always'}, True, 'local'),
    (False, {'local': True}, True, 'none'),
    (False, {'local': False, 'url': TEST_FAKE_URL, 'thumbnail_url': TEST_FAKE_THUMBNAIL_URL}, False, 'fake'),
    (False, {'local': False, 'url': TEST_FAKE_URL, 'local_thumbnail': 'always'}, False, 'local'),
    (False, {'local': False, 'url': TEST_FAKE_URL}, False, 'none'),
]


@pytest.mark.parametrize('add_trailing_bytes,params,expect_local_url,expect_thumbnail_mode', TEST_PARAMS)
@pytest.mark.asyncio
async def test_upload_auto_local_thumbnail(test_client, check_local_dir_empty, wait_for_background_task,
                                           add_trailing_bytes, params, expect_local_url, expect_thumbnail_mode):
    with open('tests/assets/test_images/bsn_0.jpg', 'rb') as f:
        img_bytes = f.read()
        # append 500KB to the image, to make it large enough to generate a thumbnail
        if add_trailing_bytes:
            img_bytes += bytearray(random.getrandbits(8) for _ in range(1024 * 500))
            f_patched = io.BytesIO(img_bytes)
            f_patched.name = 'bsn_0.jpg'
        else:
            f_patched = f
        resp = test_client.post('/admin/upload',
                                files={'image_file': f_patched},
                                headers={'x-admin-token': TEST_ADMIN_TOKEN},
                                params=params)
    assert resp.status_code == 200
    id = resp.json()['image_id']
    await wait_for_background_task(1)

    query = test_client.get('/search/random', headers={'x-access-token': TEST_ACCESS_TOKEN})
    assert query.status_code == 200
    assert query.json()['result'][0]['img']['id'] == id

    if expect_local_url:
        assert query.json()['result'][0]['img']['url'].startswith(f'/static/{id}.')
        img_request = test_client.get(query.json()['result'][0]['img']['url'])
        assert img_request.status_code == 200
    else:
        assert query.json()['result'][0]['img']['url'] == TEST_FAKE_URL

    match expect_thumbnail_mode:
        case 'local':
            assert query.json()['result'][0]['img']['thumbnail_url'] == f'/static/thumbnails/{id}.webp'

            thumbnail_request = test_client.get(query.json()['result'][0]['img']['thumbnail_url'])
            assert thumbnail_request.status_code == 200
            # IDK why starlette doesn't return the correct content type, but it works on the browser anyway
            # assert thumbnail_request.headers['Content-Type'] == 'image/webp'
        case 'fake':
            assert query.json()['result'][0]['img']['thumbnail_url'] == TEST_FAKE_THUMBNAIL_URL
        case 'none':
            assert query.json()['result'][0]['img']['thumbnail_url'] is None

    # cleanup
    resp = test_client.delete(f'/admin/delete/{id}', headers={'x-admin-token': TEST_ADMIN_TOKEN})
    assert resp.status_code == 200
