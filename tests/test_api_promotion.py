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

def get_test_manifest():
    """Get a test manifest for promotion testing"""
    manifest_path = DATA / "manifests/core/test-manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text())
    
    # Create a simple test manifest if it doesn't exist
    test_manifest = {
        "envelope": {
            "integrity": {"sha256": "sha256:test1234567890abcdef"},
            "created_at": "2025-01-01T00:00:00Z"
        },
        "objects": [
            {"hash": "sha256:test1234567890abcdef", "path": "test/object.json"}
        ]
    }
    
    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(test_manifest, indent=2))
    return test_manifest

class TestAPIPromotion:
    """Test suite for API promotion functionality"""
    
    def setup_method(self):
        """Setup test environment before each test"""
        self.client = TestClient(app)
        self.original_channels = get_channels_state()
        
    def teardown_method(self):
        """Cleanup after each test - restore original channels state"""
        channels_path = DATA / "channels.yaml"
        if self.original_channels:
            channels_path.write_text(yaml.dump(self.original_channels, default_flow_style=False))
        elif channels_path.exists():
            channels_path.unlink()
    
    def test_promote_manifest_success(self):
        """Test successful manifest promotion via API"""
        # Generate JWT with required scope
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        

        
        # Get test manifest
        manifest = get_test_manifest()
        
        # Make promotion request
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": manifest},
            headers=headers
        )
        

        
        # Verify API response
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Verify channels.yaml was updated
        updated_channels = get_channels_state()
        
        assert "core" in updated_channels
        assert "prod" in updated_channels["core"]
        assert "current" in updated_channels["core"]["prod"]
        assert "promoted_at" in updated_channels["core"]["prod"]
        
        # Verify normalized structure was stored correctly
        stored_current = updated_channels["core"]["prod"]["current"]
        
        # Check that the normalized structure was stored correctly
        assert stored_current["id"] == manifest["manifest_id"]
        assert "etag" in stored_current
        assert "promoted_at" in stored_current
        assert "by" in stored_current
    
    def test_promote_manifest_missing_auth(self):
        """Test promotion fails without authentication"""
        manifest = get_test_manifest()
        
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": manifest}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"]["error"]["code"] == "unauthorized"
    
    def test_promote_manifest_insufficient_scope(self):
        """Test promotion fails with insufficient scope"""
        # Generate JWT without channels:promote scope
        token = generate_test_jwt("objects:read manifests:read")
        headers = {"Authorization": f"Bearer {token}"}
        
        manifest = get_test_manifest()
        
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": manifest},
            headers=headers
        )
        
        assert response.status_code == 403
        assert response.json()["detail"]["error"]["code"] == "forbidden"
        assert "Missing scope: channels:promote" in response.json()["detail"]["error"]["message"]
    
    def test_promote_manifest_invalid_token(self):
        """Test promotion fails with invalid JWT"""
        headers = {"Authorization": "Bearer invalid-token"}
        
        manifest = get_test_manifest()
        
        response = self.client.post(
            "/channels/core/prod:promote",
            json={"manifest": manifest},
            headers=headers
        )
        
        assert response.status_code == 401
        assert response.json()["detail"]["error"]["code"] == "unauthorized"
    
    def test_promote_manifest_staging_environment(self):
        """Test promotion to staging environment"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        manifest = get_test_manifest()
        
        response = self.client.post(
            "/channels/core/staging:promote",
            json={"manifest": manifest},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Verify staging channel was updated
        updated_channels = get_channels_state()
        assert "core" in updated_channels
        assert "staging" in updated_channels["core"]
        assert "current" in updated_channels["core"]["staging"]
    
    def test_promote_manifest_new_dataset(self):
        """Test promotion to a new dataset"""
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        manifest = get_test_manifest()
        
        response = self.client.post(
            "/channels/newdataset/prod:promote",
            json={"manifest": manifest},
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Verify new dataset was created
        updated_channels = get_channels_state()
        assert "newdataset" in updated_channels
        assert "prod" in updated_channels["newdataset"]
        assert "current" in updated_channels["newdataset"]["prod"]
    
    def test_promote_manifest_preserves_existing_channels(self):
        """Test that promotion doesn't affect other channels"""
        # Set up initial state with multiple channels
        initial_channels = {
            "core": {
                "prod": {"current": {"id": "existing-prod", "etag": "sha256:existing-prod", "promoted_at": "2025-01-01T00:00:00Z", "by": "test"}},
                "staging": {"current": {"id": "existing-staging", "etag": "sha256:existing-staging", "promoted_at": "2025-01-01T00:00:00Z", "by": "test"}}
            },
            "other": {
                "prod": {"current": {"id": "other-prod", "etag": "sha256:other-prod", "promoted_at": "2025-01-01T00:00:00Z", "by": "test"}}
            }
        }
        
        channels_path = DATA / "channels.yaml"
        channels_path.write_text(yaml.dump(initial_channels, default_flow_style=False))
        
        # Promote to core.staging
        token = generate_test_jwt("channels:promote")
        headers = {"Authorization": f"Bearer {token}"}
        
        manifest = get_test_manifest()
        
        response = self.client.post(
            "/channels/core/staging:promote",
            json={"manifest": manifest},
            headers=headers
        )
        
        assert response.status_code == 200
        
        # Verify only core.staging was updated, others preserved
        updated_channels = get_channels_state()
        assert updated_channels["core"]["prod"]["current"]["id"] == "existing-prod"
        assert updated_channels["other"]["prod"]["current"]["id"] == "other-prod"
        assert "current" in updated_channels["core"]["staging"]
        assert updated_channels["core"]["staging"]["current"]["id"] == manifest["manifest_id"]
