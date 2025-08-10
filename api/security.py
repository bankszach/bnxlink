from __future__ import annotations
from fastapi import Header, HTTPException
from jose import jwt, JWTError
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "bnxlink"
    jwt_audience: str = "bnx-data"
    jwt_secret: str = "dev-only-not-for-prod"
    jwt_public_key: str | None = None
    jwt_private_key: str | None = None
    cors_origins: str = ""
    
    model_config = {"env_prefix": "BNX_", "env_file": ".env"}

settings = Settings()

def _decode(token: str) -> dict:
    try:
        if settings.jwt_algorithm.upper() == "RS256":
            if not settings.jwt_public_key:
                raise HTTPException(status_code=500, detail={"error":{"code":"server_config","message":"Missing BNX_JWT_PUBLIC_KEY"}})
            return jwt.decode(token, settings.jwt_public_key, algorithms=["RS256"],
                              audience=settings.jwt_audience, issuer=settings.jwt_issuer)
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"],
                          audience=settings.jwt_audience, issuer=settings.jwt_issuer)
    except JWTError:
        raise HTTPException(status_code=401, detail={"error":{"code":"unauthorized","message":"Unauthorized"}})

def require_bearer(authorization: str | None = Header(None, alias="Authorization")) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error":{"code":"unauthorized","message":"Unauthorized"}})
    claims = _decode(authorization.split(" ", 1)[1])
    scopes = claims.get("scope") or claims.get("scopes") or ""
    scope_list = [s for s in (scopes if isinstance(scopes, str) else " ".join(scopes)).split() if s]
    return {"sub": claims.get("sub"), "scopes": set(scope_list), "purpose": claims.get("purpose"), "claims": claims}

def require_scope(principal: dict, needed: str):
    if needed not in principal["scopes"]:
        raise HTTPException(status_code=403, detail={"error":{"code":"forbidden","message":f"Missing scope: {needed}"}})


