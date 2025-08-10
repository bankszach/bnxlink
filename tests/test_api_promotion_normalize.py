import json
import pathlib
import pytest
import time
import yaml
from fastapi.testclient import TestClient
from jose import jwt
from api.main import app

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def generate_test_jwt(scopes="channels:promote"):
    """Generate a test JWT token with specified scopes"""
    secret = "dev-only-not-for-prod"
    current_time = int(time.time())
    claims = {
        "iss": "bnxlink",
        "aud": "bnx-data", 
        "sub": "test-user",
        "iat": current_time,
        "exp": current_time + 3600,
        "scope": scopes,
        "purpose": "testing"
    }
    return jwt.encode(claims, secret, algorithm="HS256")

def get_channels_state():
    """Get current channels.yaml state"""
    channels_path = DATA / "channels.yaml"
    if channels_path.exists():
        return yaml.safe_load(channels_path.read_text()) or {}
    return {}

def create_test_manifest(manifest_id="test-normalize"):
    """Create a test manifest for normalization testing"""
    test_manifest = {
        "manifest_id": manifest_id,
        "dataset": "core",
        "created_at": "2025-01-01T00:00:00Z",
        "objects": [
            {"hash": f"sha256:{manifest_id}1234567890abcdef", "path": "test/object.json"}
        ]
    }
    return test_manifest

class TestAPIPromotionNormalize:
    """Test suite for API promotion normalization functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = TestClient(app)
        self.original_channels = get_channels_state()
        
        # Create a clean test environment for each test
        self.test_channels = {
            "core": {
                "prod": {},
                "staging": {}
            }
        }
        channels_path = DATA / "channels.yaml"
        channels_path.write_text(yaml.dump(self.test_channels, default_flow_style=False))
        
    def teardown_method(self):
        """Cleanup after each test - restore original channels state"""
        channels_path = DATA / "channels.yaml"
        if self.original_channels:
            channels_path.write_text(yaml.dump(self.original_channels, default_flow_style=False))
        elif channels_path.exists():
            channels_path.unlink()
        
        # Clean up any test manifests we created
        test_manifest_path = DATA / "manifests/core/test-normalize.json"
        if test_manifest_path.exists():
            test_manifest_path.unlink()
        
        test_history_path = DATA / "manifests/core/test-history.json"
        if test_history_path.exists():
            test_history_path.unlink()
    
    def test_promote_with_string_id_normalizes_structure(self):
        """Test POST with manifest ID string creates normalized channels.yaml structure"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Promote using existing manifest ID
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": "dev-seed"},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Verify channels.yaml has normalized structure
        updated_channels = get_channels_state()
        assert "core" in updated_channels
        assert "prod" in updated_channels["core"]
        
        # Check normalized current structure
        current = updated_channels["core"]["prod"]["current"]
        assert "id" in current
        assert "etag" in current
        assert "promoted_at" in current
        assert "by" in current
        
        assert current["id"] == "dev-seed"
        assert current["by"] == "test-user"
        # dev-seed manifest has objects[0].hash as etag
        assert current["etag"] == "sha256:1dc3d0e4809ec1c49d3ad5c524dadabbb5f80f9d7eb1053e3b5a0c71687f11a6"
    
    def test_promote_with_dict_creates_snapshot_and_normalizes(self):
        """Test POST with manifest dict creates snapshot file and normalized channels.yaml"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a new manifest that doesn't exist as a file
        new_manifest = create_test_manifest("test-normalize")
        
        response = self.client.post(
            "/channels/core/staging:promote",
            json={"manifest": new_manifest},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Verify snapshot file was created
        snapshot_path = DATA / "manifests/core/test-normalize.json"
        assert snapshot_path.exists()
        
        # Verify channels.yaml has normalized structure
        updated_channels = get_channels_state()
        assert "core" in updated_channels
        assert "staging" in updated_channels["core"]
        
        current = updated_channels["core"]["staging"]["current"]
        assert current["id"] == "test-normalize"
        assert current["etag"] == "sha256:test-normalize1234567890abcdef"
        assert current["by"] == "test-user"
    
    def test_promote_with_nonexistent_id_returns_404(self):
        """Test POST with non-existent manifest ID returns 404 error"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": "nonexistent-manifest"},
            headers=headers
        )
        
        assert response.status_code == 404
        error_detail = response.json()["detail"]
        assert error_detail["error"]["code"] == "not_found"
        assert "manifest not found: nonexistent-manifest" in error_detail["error"]["message"]
    
    def test_promote_with_invalid_input_returns_400(self):
        """Test POST with invalid manifest input returns 400 error"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test with None
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": None},
            headers=headers
        )
        
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert error_detail["error"]["code"] == "bad_request"
        assert "manifest must be id or object" in error_detail["error"]["message"]
        
        # Test with list
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": []},
            headers=headers
        )
        
        assert response.status_code == 400
    
    def test_promote_creates_history_on_subsequent_promotions(self):
        """Test that multiple promotions create history entries"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        # First promotion
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": "dev-seed"},
            headers=headers
        )
        assert response.status_code == 200
        
        # Second promotion with different manifest
        new_manifest = create_test_manifest("test-history")
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": new_manifest},
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify channels.yaml has history
        updated_channels = get_channels_state()
        prod_channel = updated_channels["core"]["prod"]
        
        # Should have current and history
        assert "current" in prod_channel
        assert "history" in prod_channel
        
        # Current should be the latest
        assert prod_channel["current"]["id"] == "test-history"
        
        # History should contain the previous promotion
        assert len(prod_channel["history"]) == 1
        assert prod_channel["history"][0]["id"] == "dev-seed"
    
    def test_promote_same_manifest_doesnt_create_history(self):
        """Test that promoting the same manifest doesn't create duplicate history"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        # First promotion
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": "dev-seed"},
            headers=headers
        )
        assert response.status_code == 200
        
        # Second promotion with same manifest
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": "dev-seed"},
            headers=headers
        )
        assert response.status_code == 200
        
        # Verify no history was created for same manifest
        updated_channels = get_channels_state()
        prod_channel = updated_channels["core"]["prod"]
        
        # Should only have current, no history
        assert "current" in prod_channel
        assert "history" not in prod_channel or len(prod_channel["history"]) == 0
        
        # Current should still be dev-seed
        assert prod_channel["current"]["id"] == "dev-seed"
