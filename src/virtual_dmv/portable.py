"""Small, reviewable RFC8032 Ed25519 reference implementation using Python stdlib.

RESEARCH/EDUCATION ONLY. Variable-time big integer operations, no hardening,
no audited crypto library, no secure private-key facility. NOT for real credentials.
The demo uses generated private seeds; never import real signing keys here.
"""
import base64
import hashlib
import json
import secrets

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = (-121665 * pow(121666, P - 2, P)) % P
SQRT_M1 = pow(2, (P - 1) // 4, P)
IDENTITY = (0, 1, 1, 0)


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def sha256(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def b64(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def unb64(text):
    if not isinstance(text, str) or len(text) > 256:
        raise ValueError("invalid base64url")
    if not text or any(c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in text):
        raise ValueError("invalid base64url")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _add(a, b):
    x1, y1, z1, t1 = a
    x2, y2, z2, t2 = b
    aa = ((y1 - x1) * (y2 - x2)) % P
    bb = ((y1 + x1) * (y2 + x2)) % P
    cc = (2 * D * t1 * t2) % P
    dd = (2 * z1 * z2) % P
    e, f, g, h = (bb-aa) % P, (dd-cc) % P, (dd+cc) % P, (bb+aa) % P
    return (e*f % P, g*h % P, f*g % P, e*h % P)


def _mul(point, scalar):
    acc = IDENTITY
    while scalar:
        if scalar & 1:
            acc = _add(acc, point)
        point = _add(point, point)
        scalar >>= 1
    return acc


def _xrecover(y, sign):
    xx = (y*y-1)*pow(D*y*y+1, P-2, P) % P
    x = pow(xx, (P+3)//8, P)
    if (x*x-xx) % P:
        x = x*SQRT_M1 % P
    if (x*x-xx) % P:
        raise ValueError("point not on curve")
    if x == 0 and sign:
        raise ValueError("negative zero point")
    if (x & 1) != sign:
        x = P-x
    return x


def _decode(raw):
    if len(raw) != 32:
        raise ValueError("invalid point length")
    v = int.from_bytes(raw, "little")
    sign = v >> 255
    y = v & ((1 << 255)-1)
    if y >= P:
        raise ValueError("noncanonical point")
    x = _xrecover(y, sign)
    return x, y, 1, x*y % P


def _encode(point):
    x, y, z, _ = point
    inv_z = pow(z, P-2, P)
    x = x*inv_z % P
    y = y*inv_z % P
    return (y | ((x & 1) << 255)).to_bytes(32, "little")


_BASE_Y = 4 * pow(5, P-2, P) % P
_BASE_X = _xrecover(_BASE_Y, 0)
BASE = (_BASE_X, _BASE_Y, 1, _BASE_X*_BASE_Y % P)


def make_seed():
    return b64(secrets.token_bytes(32))


def _scalar(seed):
    h = hashlib.sha512(seed).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254)-8
    a |= 1 << 254
    return a, h[32:]


def public_key(seed_text):
    seed = unb64(seed_text)
    if len(seed) != 32:
        raise ValueError("private seed must be 32 bytes")
    a, _ = _scalar(seed)
    return b64(_encode(_mul(BASE, a)))


def sign(seed_text, payload):
    seed = unb64(seed_text)
    if len(seed) != 32:
        raise ValueError("private seed must be 32 bytes")
    a, prefix = _scalar(seed)
    message = canonical(payload)
    a_bytes = _encode(_mul(BASE, a))
    r = int.from_bytes(hashlib.sha512(prefix+message).digest(), "little") % L
    r_bytes = _encode(_mul(BASE, r))
    k = int.from_bytes(hashlib.sha512(r_bytes+a_bytes+message).digest(), "little") % L
    return b64(r_bytes + ((r+k*a) % L).to_bytes(32, "little"))


def verify(pub_text, payload, signature):
    try:
        public, sig = unb64(pub_text), unb64(signature)
        if len(public) != 32 or len(sig) != 64:
            return False
        aa, rr = _decode(public), _decode(sig[:32])
        s = int.from_bytes(sig[32:], "little")
        if s >= L:
            return False
        # Reject small order and non-prime-order public/R points.
        if _encode(_mul(aa, L)) != _encode(IDENTITY) or _encode(aa) == _encode(IDENTITY):
            return False
        if _encode(_mul(rr, L)) != _encode(IDENTITY):
            return False
        k = int.from_bytes(hashlib.sha512(sig[:32]+public+canonical(payload)).digest(), "little") % L
        return _encode(_mul(BASE, s)) == _encode(_add(rr, _mul(aa, k)))
    except (ValueError, TypeError, KeyError, OverflowError):
        return False
