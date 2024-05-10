import asyncio
from pathlib import Path

import pytest

from .conftest import TEST_ADMIN_TOKEN, TEST_ACCESS_TOKEN

assets_path = Path(__file__).parent / '..' / 'assets'

test_images = {'bsn': ['bsn_0.jpg', 'bsn_1.jpg', 'bsn_2.jpg'],
               'cat': ['cat_0.jpg', 'cat_1.jpg'],
               'cg': ['cg_0.jpg', 'cg_1.png']}


@pytest.mark.asyncio
async def test_integrate(test_client):
    credentials = {'x-admin-token': TEST_ADMIN_TOKEN, 'x-access-token': TEST_ACCESS_TOKEN}
    img_ids = dict()
    for img_cls in test_images:
        img_ids[img_cls] = []
        for image in test_images[img_cls]:
            print(f'upload image {image}...')
            resp = test_client.post('/admin/upload',
                                    files={'image_file': open(assets_path / 'test_images' / image, 'rb')},
                                    headers=credentials,
                                    params={'local': True})
            assert resp.status_code == 200
            img_ids[img_cls].append(resp.json()['image_id'])

    print('Waiting for images to be processed...')

    while True:
        resp = test_client.get('/admin/server_info', headers=credentials)
        if resp.json()['image_count'] >= 7:
            break
        await asyncio.sleep(1)

    resp = test_client.get('/search/text/hatsune+miku',
                           headers=credentials)
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['cg']

    resp = test_client.post('/search/image',
                            files={'image': open(assets_path / 'test_images' / test_images['cat'][0], 'rb')},
                            headers=credentials)

    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['cat']

    resp = test_client.get(f"/search/similar/{img_ids['bsn'][0]}",
                           headers=credentials)

    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']

    resp = test_client.put(f"/admin/update_opt/{img_ids['bsn'][0]}", json={'categories': ['bsn'], 'starred': True},
                           headers=credentials)
    assert resp.status_code == 200

    resp = test_client.get(f"/search/text/cat", params={'categories': 'bsn'}, headers=credentials)
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']

    resp = test_client.get(f"/search/text/cat", params={'starred': True}, headers=credentials)
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']
