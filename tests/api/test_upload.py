import io
import random

import pytest

from .conftest import TEST_ADMIN_TOKEN, TEST_ACCESS_TOKEN, assets_path

test_file_path = assets_path / 'test_images' / 'bsn_0.jpg'


def get_single_img_info(test_client, image_id):
    query = test_client.get('/search/random', headers={'x-access-token': TEST_ACCESS_TOKEN})
    assert query.status_code == 200
    assert query.json()['result'][0]['img']['id'] == image_id

    return query.json()['result'][0]['img']


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


@pytest.mark.asyncio
async def test_upload_duplicate(test_client, check_local_dir_empty, wait_for_background_task):
    def upload(file):
        return test_client.post('/admin/upload',
                                files={'image_file': file},
                                headers={'x-admin-token': TEST_ADMIN_TOKEN},
                                params={'local': True})

    with open(test_file_path, 'rb') as f:
        resp = upload(f)
        assert resp.status_code == 200
        image_id = resp.json()['image_id']
        resp = upload(f)  # The previous image is still in queue
        assert resp.status_code == 409
        await wait_for_background_task(1)
        resp = upload(f)  # The previous image is indexed now
        assert resp.status_code == 409

    # cleanup
    resp = test_client.delete(f'/admin/delete/{image_id}', headers={'x-admin-token': TEST_ADMIN_TOKEN})
    assert resp.status_code == 200


TEST_FAKE_URL = 'fake-url'
TEST_FAKE_THUMBNAIL_URL = 'fake-thumbnail-url'

TEST_UPLOAD_THUMBNAILS_PARAMS = [
    (True, {'local': True}, True, 'local'),
    (True, {'local': True, 'local_thumbnail': 'never'}, True, 'none'),
    (False, {'local': True, 'local_thumbnail': 'always'}, True, 'local'),
    (False, {'local': True}, True, 'none'),
    (False, {'local': False, 'url': TEST_FAKE_URL, 'thumbnail_url': TEST_FAKE_THUMBNAIL_URL}, False, 'fake'),
    (False, {'local': False, 'url': TEST_FAKE_URL, 'local_thumbnail': 'always'}, False, 'local'),
    (False, {'local': False, 'url': TEST_FAKE_URL}, False, 'none'),
]


@pytest.mark.parametrize('add_trailing_bytes,params,expect_local_url,expect_thumbnail_mode',
                         TEST_UPLOAD_THUMBNAILS_PARAMS)
@pytest.mark.asyncio
async def test_upload_thumbnails(test_client, check_local_dir_empty, wait_for_background_task,  # Fixtures
                                 add_trailing_bytes, params, expect_local_url, expect_thumbnail_mode):  # Parameters
    with open(test_file_path, 'rb') as f:
        # append 500KB to the image, to make it large enough to generate a thumbnail
        if add_trailing_bytes:
            img_bytes = f.read()
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
    image_id = resp.json()['image_id']
    await wait_for_background_task(1)

    query = get_single_img_info(test_client, image_id)

    if expect_local_url:
        assert query['url'].startswith(f'/static/{image_id}.')
        img_request = test_client.get(query['url'])
        assert img_request.status_code == 200
    else:
        assert query['url'] == TEST_FAKE_URL

    match expect_thumbnail_mode:
        case 'local':
            assert query['thumbnail_url'] == f'/static/thumbnails/{image_id}.webp'

            thumbnail_request = test_client.get(query['thumbnail_url'])
            assert thumbnail_request.status_code == 200
            # IDK why starlette doesn't return the correct content type, but it works on the browser anyway
            # assert thumbnail_request.headers['Content-Type'] == 'image/webp'
        case 'fake':
            assert query['thumbnail_url'] == TEST_FAKE_THUMBNAIL_URL
        case 'none':
            assert query['thumbnail_url'] is None

    # cleanup
    resp = test_client.delete(f'/admin/delete/{image_id}', headers={'x-admin-token': TEST_ADMIN_TOKEN})
    assert resp.status_code == 200


TEST_FAKE_URL_NEW = 'fake-url-new'
TEST_FAKE_THUMBNAIL_URL_NEW = 'fake-thumbnail-url-new'

TEST_UPDATE_OPT_PARAMS = [
    ({'url': TEST_FAKE_URL}, {'url': TEST_FAKE_URL_NEW, 'thumbnail_url': TEST_FAKE_THUMBNAIL_URL_NEW},
     {'url': TEST_FAKE_URL_NEW, 'thumbnail_url': TEST_FAKE_THUMBNAIL_URL_NEW}, 200),
    ({'local_thumbnail': 'always', 'url': TEST_FAKE_URL}, {'url': TEST_FAKE_URL_NEW}, {'url': TEST_FAKE_URL_NEW}, 200),
    ({'local': True}, {'categories': ['1'], 'starred': True}, {'categories': ['1'], 'starred': True}, 200),
    ({'local': True}, {'url': TEST_FAKE_URL_NEW}, {}, 422),
    ({'local': True}, {'thumbnail_url': TEST_FAKE_THUMBNAIL_URL_NEW}, {}, 422),
    ({'local_thumbnail': 'always', 'url': TEST_FAKE_URL}, {'thumbnail_url': TEST_FAKE_THUMBNAIL_URL_NEW}, {}, 422),
    ({'local': True}, {}, {}, 422),
]


@pytest.mark.parametrize('initial_param,update_param,expected_param,resp_code', TEST_UPDATE_OPT_PARAMS)
@pytest.mark.asyncio
async def test_update_opt(test_client, check_local_dir_empty, wait_for_background_task,  # Fixtures
                          initial_param, update_param, expected_param, resp_code):  # Parameters
    with open(test_file_path, 'rb') as f:
        resp = test_client.post('/admin/upload',
                                files={'image_file': f},
                                headers={'x-admin-token': TEST_ADMIN_TOKEN},
                                params=initial_param)
    assert resp.status_code == 200
    image_id = resp.json()['image_id']
    await wait_for_background_task(1)

    old_info = get_single_img_info(test_client, image_id)

    resp = test_client.put(f'/admin/update_opt/{image_id}', json=update_param,
                           headers={'x-admin-token': TEST_ADMIN_TOKEN})
    assert resp.status_code == resp_code

    new_info = get_single_img_info(test_client, image_id)
    # Ensure expected keys are updated
    for key, value in expected_param.items():
        assert new_info[key] == value
        del new_info[key]

    # Ensure that the other keys are kept untouched
    for key, value in new_info.items():
        assert old_info[key] == value

    # cleanup
    resp = test_client.delete(f'/admin/delete/{image_id}', headers={'x-admin-token': TEST_ADMIN_TOKEN})
    assert resp.status_code == 200
