import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.api_key import ApiKey


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    response = client.post('/api/auth/login', json={
        "username": "admin",
        "password": "admin123"
    })
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestApiKeyModel:
    def test_generate_key(self):
        raw_key, prefix, key_hash = ApiKey.generate_key()
        assert raw_key.startswith("sk_")
        assert len(raw_key) == 67  # "sk_" + 64 hex chars
        assert prefix == raw_key[:8]
        assert len(key_hash) == 64

    def test_hash_key_consistent(self):
        raw_key, _, key_hash = ApiKey.generate_key()
        assert ApiKey.hash_key(raw_key) == key_hash

    def test_hash_key_different_keys(self):
        _, _, hash1 = ApiKey.generate_key()
        _, _, hash2 = ApiKey.generate_key()
        assert hash1 != hash2


class TestApiKeyRoutes:
    def test_create_api_key(self, client, auth_headers):
        response = client.post('/api/api-keys', json={"name": "Test Key"}, headers=auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Test Key"
        assert "key" in data
        assert data["key"].startswith("sk_")
        assert data["is_active"] is True
        assert "key_hash" not in data

    def test_create_api_key_requires_name(self, client, auth_headers):
        response = client.post('/api/api-keys', json={}, headers=auth_headers)
        assert response.status_code == 400

    def test_list_api_keys(self, client, auth_headers):
        client.post('/api/api-keys', json={"name": "Key 1"}, headers=auth_headers)
        client.post('/api/api-keys', json={"name": "Key 2"}, headers=auth_headers)
        response = client.get('/api/api-keys', headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

    def test_list_api_keys_does_not_expose_hash(self, client, auth_headers):
        client.post('/api/api-keys', json={"name": "Key 1"}, headers=auth_headers)
        response = client.get('/api/api-keys', headers=auth_headers)
        data = response.get_json()
        assert "key_hash" not in data[0]

    def test_revoke_api_key(self, client, auth_headers):
        create_resp = client.post('/api/api-keys', json={"name": "To Revoke"}, headers=auth_headers)
        key_id = create_resp.get_json()["id"]
        response = client.delete(f'/api/api-keys/{key_id}', headers=auth_headers)
        assert response.status_code == 200
        # Verify it's now inactive
        list_resp = client.get('/api/api-keys', headers=auth_headers)
        keys = list_resp.get_json()
        revoked = [k for k in keys if k["id"] == key_id][0]
        assert revoked["is_active"] is False

    def test_create_api_key_with_expiry(self, client, auth_headers):
        response = client.post('/api/api-keys', json={
            "name": "Expiring Key",
            "expires_at": "2030-12-31T23:59:59"
        }, headers=auth_headers)
        assert response.status_code == 201
        data = response.get_json()
        assert data["expires_at"] is not None


class TestApiKeyAuth:
    def test_api_key_auth_grants_access(self, client, auth_headers):
        create_resp = client.post('/api/api-keys', json={"name": "Auth Test"}, headers=auth_headers)
        raw_key = create_resp.get_json()["key"]
        # Use API key to access a protected endpoint
        response = client.get('/api/customers', headers={"X-API-Key": raw_key})
        assert response.status_code == 200

    def test_invalid_api_key_rejected(self, client):
        response = client.get('/api/customers', headers={"X-API-Key": "sk_invalid"})
        assert response.status_code == 401

    def test_revoked_api_key_rejected(self, client, auth_headers):
        create_resp = client.post('/api/api-keys', json={"name": "Revoke Test"}, headers=auth_headers)
        raw_key = create_resp.get_json()["key"]
        key_id = create_resp.get_json()["id"]
        # Revoke it
        client.delete(f'/api/api-keys/{key_id}', headers=auth_headers)
        # Try using the revoked key
        response = client.get('/api/customers', headers={"X-API-Key": raw_key})
        assert response.status_code == 401

    def test_api_key_updates_last_used(self, client, auth_headers):
        create_resp = client.post('/api/api-keys', json={"name": "Usage Test"}, headers=auth_headers)
        raw_key = create_resp.get_json()["key"]
        key_id = create_resp.get_json()["id"]
        # Use the key
        client.get('/api/customers', headers={"X-API-Key": raw_key})
        # Check last_used_at is set
        list_resp = client.get('/api/api-keys', headers=auth_headers)
        keys = list_resp.get_json()
        used_key = [k for k in keys if k["id"] == key_id][0]
        assert used_key["last_used_at"] is not None

    def test_no_auth_rejected(self, client):
        response = client.get('/api/customers')
        assert response.status_code == 401
