from pathlib import Path

import pytest

from .conftest import TEST_ADMIN_TOKEN, TEST_ACCESS_TOKEN

assets_path = Path(__file__).parent / '..' / 'assets'

test_images = {'bsn': ['bsn_0.jpg', 'bsn_1.jpg', 'bsn_2.jpg'],
               'cat': ['cat_0.jpg', 'cat_1.jpg'],
               'cg': ['cg_0.jpg', 'cg_1.png']}


@pytest.mark.asyncio
async def test_search(test_client, check_local_dir_empty, wait_for_background_task):
    credentials = {'x-admin-token': TEST_ADMIN_TOKEN, 'x-access-token': TEST_ACCESS_TOKEN}
    resp = test_client.get("/", headers=credentials)
    assert resp.status_code == 200
    img_ids = {}
    for img_cls, item_images in test_images.items():
        img_ids[img_cls] = []
        for image in item_images:
            print(f'upload image {image}...')
            with open(assets_path / 'test_images' / image, 'rb') as f:
                resp = test_client.post('/admin/upload',
                                        files={'image_file': f},
                                        headers=credentials,
                                        params={'local': True})
            assert resp.status_code == 200
            img_ids[img_cls].append(resp.json()['image_id'])

    print('Waiting for images to be processed...')

    await wait_for_background_task(sum(len(v) for v in test_images.values()))

    resp = test_client.get('/search/text/hatsune+miku',
                           headers=credentials)
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['cg']

    with open(assets_path / 'test_images' / test_images['cat'][0], 'rb') as f:
        resp = test_client.post('/search/image',
                                files={'image': f},
                                headers=credentials)

    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['cat']

    resp = test_client.get(f"/search/similar/{img_ids['bsn'][0]}",
                           headers=credentials)

    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']

    image_request = test_client.get(resp.json()['result'][0]['img']['url'])
    assert image_request.status_code == 200
    assert image_request.headers['Content-Type'] == 'image/jpeg'

    resp = test_client.put(f"/admin/update_opt/{img_ids['bsn'][0]}", json={'categories': ['bsn'], 'starred': True},
                           headers=credentials)
    assert resp.status_code == 200

    resp = test_client.get("/search/text/cat", params={'categories': 'bsn'}, headers=credentials)
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']

    resp = test_client.get("/search/text/cat", params={'starred': True}, headers=credentials)
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']

    resp = test_client.delete(f"/admin/delete/{img_ids['bsn'][0]}", headers=credentials)
    assert resp.status_code == 200

    resp = test_client.get("/search/text/cat", params={'categories': 'bsn'}, headers=credentials)
    assert resp.status_code == 200
    assert len(resp.json()['result']) == 0

    # cleanup
    for img_cls in test_images.keys():
        for img_id in img_ids[img_cls]:
            resp = test_client.delete(f"/admin/delete/{img_id}", headers=credentials)
            assert resp.status_code == (404 if img_id == img_ids['bsn'][0] else 200)
