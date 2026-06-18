"""RSA keys for OIDC RS256 tokens."""

from functools import lru_cache

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk

from app.core.config import settings


@lru_cache
def get_oidc_private_key_pem() -> str:
    """Вернуть PEM приватного RSA ключа."""
    if settings.oidc_private_key_pem.strip():
        return settings.oidc_private_key_pem.strip()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


@lru_cache
def get_oidc_public_jwks() -> dict:
    """JWKS document for OIDC discovery."""
    private_key = serialization.load_pem_private_key(
        get_oidc_private_key_pem().encode("utf-8"),
        password=None,
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    key = jwk.construct(public_pem, algorithm="RS256")
    return {"keys": [key.to_dict()]}
