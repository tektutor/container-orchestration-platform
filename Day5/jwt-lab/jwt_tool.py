#!/usr/bin/env python3
"""Decode and verify Kubernetes/OpenShift service account JWTs.

Standard library only (no pip installs needed).

Usage:
  python3 jwt_tool.py decode <token | ->
  python3 jwt_tool.py verify <token | -> <jwks.json>

Pass "-" to read the token from stdin.
"""
import base64
import hashlib
import json
import sys
import time

# ASN.1 DigestInfo prefix for SHA-256 (RFC 8017, section 9.2)
SHA256_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


def b64url_decode(part):
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


def read_token(arg):
    token = sys.stdin.read() if arg == "-" else arg
    token = token.strip()
    if token.count(".") != 2:
        sys.exit("Not a JWT: expected 3 dot-separated parts, got %d.\n"
                 "OpenShift OAuth user tokens (sha256~...) are opaque, not JWTs."
                 % (token.count(".") + 1))
    return token


def fmt_time(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(ts))


def decode(token):
    h, p, _ = token.split(".")
    header = json.loads(b64url_decode(h))
    payload = json.loads(b64url_decode(p))
    print("=== HEADER ===")
    print(json.dumps(header, indent=2))
    print("=== PAYLOAD ===")
    print(json.dumps(payload, indent=2))
    print("=== TIMES ===")
    now = int(time.time())
    for claim in ("iat", "nbf", "exp", "warnafter"):
        if claim in payload:
            print("%-9s %s" % (claim, fmt_time(payload[claim])))
    if "exp" in payload:
        left = payload["exp"] - now
        if left > 0:
            print("status    valid for %dm %ds" % (left // 60, left % 60))
        else:
            print("status    EXPIRED %dm %ds ago" % (-left // 60, -left % 60))
    else:
        print("status    no exp claim: this token never expires")


def verify(token, jwks_path):
    h, p, s = token.split(".")
    header = json.loads(b64url_decode(h))
    if header.get("alg") != "RS256":
        sys.exit("Unsupported alg %s: this tool verifies RS256 only" % header.get("alg"))
    with open(jwks_path) as f:
        keys = json.load(f).get("keys", [])
    key = next((k for k in keys if k.get("kid") == header.get("kid")), None)
    if key is None:
        sys.exit("FAIL: no key with kid %s in %s" % (header.get("kid"), jwks_path))

    n = int.from_bytes(b64url_decode(key["n"]), "big")
    e = int.from_bytes(b64url_decode(key["e"]), "big")
    k = (n.bit_length() + 7) // 8
    sig = int.from_bytes(b64url_decode(s), "big")

    # RSASSA-PKCS1-v1_5 verification: sig^e mod n must equal the padded digest
    em = pow(sig, e, n).to_bytes(k, "big")
    digest = hashlib.sha256((h + "." + p).encode()).digest()
    t = SHA256_PREFIX + digest
    expected = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t

    print("kid       %s" % header["kid"])
    if em == expected:
        print("signature VALID (signed by the cluster's service account key)")
    else:
        sys.exit("signature INVALID (token altered or signed by another key)")


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("decode", "verify"):
        sys.exit(__doc__)
    token = read_token(sys.argv[2])
    if sys.argv[1] == "decode":
        decode(token)
    else:
        if len(sys.argv) != 4:
            sys.exit(__doc__)
        verify(token, sys.argv[3])


if __name__ == "__main__":
    main()
