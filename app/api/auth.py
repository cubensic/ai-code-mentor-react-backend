from fastapi import HTTPException, Depends, Header
from typing import Optional
from jose import jwt, JWTError
import httpx
from datetime import datetime, timedelta
from app.config import settings

# Cache for JWKS (refreshes when needed)
_jwks_cache = None
_jwks_cache_time = None

async def get_clerk_jwks():
    """Fetch Clerk JWKS and cache it for 1 hour"""
    global _jwks_cache, _jwks_cache_time
    
    # Return cached JWKS if it's less than 1 hour old
    if _jwks_cache and _jwks_cache_time:
        if datetime.utcnow() - _jwks_cache_time < timedelta(hours=1):
            return _jwks_cache
    
    # Fetch JWKS from Clerk
    jwks_url = f"{settings.CLERK_ISSUER_URL}/.well-known/jwks.json"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url, timeout=5.0)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_cache_time = datetime.utcnow()
            return _jwks_cache
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch Clerk JWKS: {str(e)}"
        )

def get_signing_key(token: str, jwks: dict):
    """Get the signing key from JWKS for the token"""
    try:
        # Decode token header to get the key ID (kid)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(status_code=401, detail="Token missing key ID")
        
        # Find the key in JWKS
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                # Convert JWK to PEM format for python-jose
                from jose.constants import ALGORITHMS
                from cryptography.hazmat.primitives.asymmetric import rsa
                from cryptography.hazmat.backends import default_backend
                import base64
                
                # Extract RSA key components
                n = base64.urlsafe_b64decode(key["n"] + "==")
                e = base64.urlsafe_b64decode(key["e"] + "==")
                
                # Convert to RSA public key
                public_numbers = rsa.RSAPublicNumbers(
                    int.from_bytes(e, "big"),
                    int.from_bytes(n, "big")
                )
                public_key = public_numbers.public_key(default_backend())
                
                return public_key
        
        raise HTTPException(status_code=401, detail="Unable to find signing key")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token header: {str(e)}")

async def verify_clerk_token(
    authorization: Optional[str] = Header(None, alias="Authorization")
) -> str:
    """
    Verify Clerk JWT token and return Clerk user ID.
    Raises HTTPException if token is invalid.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format. Expected 'Bearer <token>'")
    
    token = authorization.replace("Bearer ", "").strip()
    
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    
    try:
        # Get JWKS from Clerk
        jwks = await get_clerk_jwks()
        
        # Get the signing key
        signing_key = get_signing_key(token, jwks)
        
        # Decode and verify the token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=None,  # Clerk doesn't use audience
            issuer=settings.CLERK_ISSUER_URL,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True
            }
        )
        
        # Extract Clerk user ID from "sub" claim
        clerk_user_id = payload.get("sub")
        if not clerk_user_id:
            raise HTTPException(status_code=401, detail="Token missing user ID (sub claim)")
        
        return clerk_user_id
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")