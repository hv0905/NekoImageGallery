import io
import random

from .conftest import TEST_ADMIN_TOKEN


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
