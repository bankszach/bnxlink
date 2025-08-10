#!/usr/bin/env python
from __future__ import annotations
from jose import jwt
from datetime import datetime, timedelta, timezone
import os, argparse

SECRET = os.environ.get("BNX_DEV_JWT_SECRET", "dev-only-not-for-prod")
ALGO = "HS256"
AUD = "bnx-data"

ap = argparse.ArgumentParser()
ap.add_argument("--sub", default="user:dev")
ap.add_argument("--scope", default="objects:read:redacted manifests:read channels:promote")
ap.add_argument("--purpose", default="analysis")
ap.add_argument("--ttl", type=int, default=3600)
args = ap.parse_args()

now = datetime.now(tz=timezone.utc)
claims = {
    "iss": "bnxlink-dev",
    "sub": args.sub,
    "aud": AUD,
    "scope": args.scope,
    "purpose": args.purpose,
    "iat": int(now.timestamp()),
    "exp": int((now + timedelta(seconds=args.ttl)).timestamp()),
}
print(jwt.encode(claims, SECRET, algorithm=ALGO))


