import pytest
from unittest.mock import patch
from fastapi import HTTPException
from api.security import _decode, settings

def test_rs256_decode_path(monkeypatch):
    # Mock settings for RS256
    monkeypatch.setattr(settings, "jwt_algorithm", "RS256")
    monkeypatch.setattr(settings, "jwt_public_key", "-----BEGIN PUBLIC KEY-----\nfake\n-----END PUBLIC KEY-----")
    
    # This should fail with JWT decode error, but not with missing key error
    try:
        _decode("invalid.token.here")
        assert False, "Should have raised 401 for invalid JWT"
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail["error"]["code"] == "unauthorized"

def test_rs256_missing_public_key_raises_500(monkeypatch):
    # Mock settings for RS256 but no public key
    monkeypatch.setattr(settings, "jwt_algorithm", "RS256")
    monkeypatch.setattr(settings, "jwt_public_key", None)
    
    try:
        _decode("any.token")
        assert False, "Should have raised 500 for missing public key"
    except HTTPException as e:
        assert e.status_code == 500
        assert e.detail["error"]["code"] == "server_config"

def test_hs256_decode_path(monkeypatch):
    # Mock settings for HS256
    monkeypatch.setattr(settings, "jwt_algorithm", "HS256")
    monkeypatch.setattr(settings, "jwt_secret", "test-secret")
    
    try:
        _decode("invalid.token.here")
        assert False, "Should have raised 401 for invalid JWT"
    except HTTPException as e:
        assert e.status_code == 401
        assert e.detail["error"]["code"] == "unauthorized"
