import itertools
import uuid

import pytest_asyncio

from .conftest import check_local_dir_empty
from ..assets import assets_path

test_images = {'bsn': ['bsn_0.jpg', 'bsn_1.jpg', 'bsn_2.jpg'],
               'cat': ['cat_0.jpg', 'cat_1.jpg'],
               'cg': ['cg_0.jpg', 'cg_1.png']}


@pytest_asyncio.fixture(scope="module")
async def img_ids(test_client, wait_for_background_task):
    img_ids = {}
    for img_cls, item_images in test_images.items():
        img_ids[img_cls] = []
        for image in item_images:
            print(f'upload image {image}...')
            with open(assets_path / 'test_images' / image, 'rb') as f:
                resp = test_client.post('/admin/upload',
                                        files={'image_file': f},
                                        params={'local': True})
            assert resp.status_code == 200
            img_ids[img_cls].append(resp.json()['image_id'])

    print('Waiting for images to be processed...')

    await wait_for_background_task(sum(len(v) for v in test_images.values()))

    yield img_ids

    # cleanup
    for img_cls in test_images.keys():
        for img_id in img_ids[img_cls]:
            resp = test_client.delete(f"/admin/delete/{img_id}")
            assert resp.status_code == 200

    check_local_dir_empty()


def test_search_text(test_client, img_ids):
    resp = test_client.get('/search/text/hatsune+miku')
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['cg']


def test_search_image(test_client, img_ids):
    with open(assets_path / 'test_images' / test_images['cat'][0], 'rb') as f:
        resp = test_client.post('/search/image',
                                files={'image': f})

    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['cat']


def test_search_similar(test_client, img_ids):
    resp = test_client.get(f"/search/similar/{img_ids['bsn'][0]}")

    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']


def test_search_advanced(test_client, img_ids):
    resp = test_client.post("/search/advanced",
                            json={'criteria': ['white background', 'grayscale image'],
                                  'negative_criteria': ['cat', 'hatsune miku']})
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] in img_ids['bsn']


def test_search_combined(test_client, img_ids):
    resp = test_client.post('/search/combined', json={'criteria': ['hatsune miku'],
                                                      'negative_criteria': ['grayscale image', 'cat'],
                                                      'extra_prompt': 'hatsunemiku'})

    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] == img_ids['cg'][1]

    resp = test_client.post('/search/combined?basis=ocr',
                            json={'criteria': ['hatsunemiku'], 'extra_prompt': 'hatsune miku'})
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] == img_ids['cg'][1]


def test_search_filters(test_client, img_ids):
    resp = test_client.put(f"/admin/update_opt/{img_ids['bsn'][0]}", json={'categories': ['bsn'], 'starred': True})
    assert resp.status_code == 200

    resp = test_client.get("/search/text/cat", params={'categories': 'bsn'})
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] == img_ids['bsn'][0]

    resp = test_client.get("/search/text/cat", params={'starred': True})
    assert resp.status_code == 200
    assert resp.json()['result'][0]['img']['id'] == img_ids['bsn'][0]


def test_images_query_by_id(test_client, img_ids):
    resp = test_client.get(f"/images/id/{img_ids['bsn'][0]}")
    assert resp.status_code == 200
    assert resp.json()['img']['id'] == img_ids['bsn'][0]


def test_images_query_not_exist(test_client, img_ids):
    resp = test_client.get(f"/images/id/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_images_query_scroll(test_client, img_ids):
    resp = test_client.get("/images/", params={'count': 50})
    assert resp.status_code == 200
    all_images_id = list(itertools.chain(*img_ids.values()))
    for item in resp.json()['images']:
        assert item['id'] in all_images_id
