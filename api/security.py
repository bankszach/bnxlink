from __future__ import annotations
from datetime import datetime, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends, Header

ALGO = "HS256"  # dev-only; swap to RS256 + JWKS later
AUDIENCE = "bnx-data"
DEV_SECRET = "dev-only-not-for-prod"  # override via BNX_DEV_JWT_SECRET env


class Principal:
    def __init__(self, sub: str, scope: list[str], purpose: str | None):
        self.sub = sub
        self.scope = scope
        self.purpose = purpose


def verify(token: str) -> Principal:
    secret = __import__("os").environ.get("BNX_DEV_JWT_SECRET", DEV_SECRET)
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[ALGO],
            audience=AUDIENCE,
            options={"verify_exp": True},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"invalid token: {e}"
        )

    exp = claims.get("exp")
    if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
        tz=timezone.utc
    ):
        raise HTTPException(status_code=401, detail="token expired")

    scope = claims.get("scope", "")
    scope_list = scope.split() if isinstance(scope, str) else list(scope or [])
    return Principal(
        sub=claims.get("sub", "unknown"), scope=scope_list, purpose=claims.get("purpose")
    )


def bearer(auth: str = Header(..., alias="Authorization")) -> Principal:
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer")
    token = auth.split(" ", 1)[1]
    return verify(token)


