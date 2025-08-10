#!/usr/bin/env python
from __future__ import annotations
import os, sys, time
from jose import jwt

ALG = os.getenv("BNX_JWT_ALGORITHM","HS256").upper()
ISS = os.getenv("BNX_JWT_ISSUER","bnxlink")
AUD = os.getenv("BNX_JWT_AUDIENCE","bnx-data")
SUB = os.getenv("BNX_DEV_SUBJECT","dev-user")
SCOPES = os.getenv("BNX_DEV_SCOPES","objects:read objects:read:redacted manifests:read channels:promote")
PURPOSE = os.getenv("BNX_DEV_PURPOSE","analysis")
TTL = int(os.getenv("BNX_DEV_TTL_SECONDS","86400"))

claims = {"iss":ISS,"aud":AUD,"sub":SUB,"iat":int(time.time()),"exp":int(time.time())+TTL,"scope":SCOPES,"purpose":PURPOSE}

if ALG == "RS256":
    priv = os.getenv("BNX_JWT_PRIVATE_KEY")
    if not priv: print("Missing BNX_JWT_PRIVATE_KEY for RS256", file=sys.stderr); sys.exit(2)
    print(jwt.encode(claims, priv, algorithm="RS256"))
else:
    secret = os.getenv("BNX_JWT_SECRET","dev-only-not-for-prod")
    print(jwt.encode(claims, secret, algorithm="HS256"))


