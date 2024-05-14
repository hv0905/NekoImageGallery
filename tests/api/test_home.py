class TestHome:

    def test_get_home_no_tokens(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.json()['authorization']['required']
        assert not response.json()['authorization']['passed']
        assert response.json()['admin_api']['available']
        assert not response.json()['admin_api']['passed']

    def test_get_home_access_token(self, test_client):
        response = test_client.get("/", headers={'x-access-token': 'test_token'})
        assert response.status_code == 200
        assert response.json()['authorization']['required']
        assert response.json()['authorization']['passed']

    def test_get_home_admin_token(self, test_client):
        response = test_client.get("/", headers={'x-admin-token': 'test_admin_token', 'x-access-token': 'test_token'})
        assert response.status_code == 200
        assert response.json()['admin_api']['available']
        assert response.json()['admin_api']['passed']
        assert response.json()['authorization']['required']
        assert response.json()['authorization']['passed']
