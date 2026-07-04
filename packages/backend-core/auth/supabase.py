from supabase import create_client, Client
from jose import jwt
from typing import Optional, Dict, Any
import logging
import httpx
import time

logger = logging.getLogger(__name__)

class SupabaseAuthenticator:
    """
    Handles authentication token validations using cached JWKS (asymmetric ES256/RS256),
    local HS256 signature verification, or remote Supabase auth token check fallback.
    """
    def __init__(
        self, 
        supabase_url: str, 
        supabase_anon_key: str, 
        jwt_secret: Optional[str] = None
    ):
        self.supabase_url = supabase_url
        self.supabase_anon_key = supabase_anon_key
        self.jwt_secret = jwt_secret
        self.jwks_url = f"{supabase_url}/auth/v1/certs"
        self._jwks_cache = None
        self._jwks_fetched_at = 0.0
        self.client: Client = create_client(supabase_url, supabase_anon_key)

    def _get_jwks(self) -> Dict[str, Any]:
        """
        Retrieves and caches JWKS public keys from Supabase Auth Server (Expires in 1 hour).
        """
        now = time.time()
        if not self._jwks_cache or (now - self._jwks_fetched_at > 3600.0):
            try:
                # Fetch public certificates from Supabase issuer
                r = httpx.get(self.jwks_url, timeout=5.0)
                if r.status_code == 200:
                    self._jwks_cache = r.json()
                    self._jwks_fetched_at = now
                    logger.info("Successfully refreshed Supabase JWKS cache.")
            except Exception as e:
                logger.error(f"Failed to retrieve JWKS certificates: {e}")
        return self._jwks_cache or {"keys": []}

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify the authorization token and return claims dictionary, or None if invalid.
        """
        # 1. Verify using Cached JWKS (Preferred - Asymmetric signature)
        jwks = self._get_jwks()
        if jwks and "keys" in jwks:
            try:
                unverified_header = jwt.get_unverified_header(token)
                kid = unverified_header.get("kid")
                if kid:
                    for key in jwks["keys"]:
                        if key.get("kid") == kid:
                            claims = jwt.decode(
                                token,
                                key,
                                algorithms=["RS256", "ES256"],
                                options={"verify_aud": False}
                            )
                            return claims
            except Exception as e:
                logger.debug(f"JWKS verification check bypassed or failed: {e}")

        # 2. Fallback to shared secret if symmetric HS256 signature is configured
        if self.jwt_secret:
            try:
                claims = jwt.decode(
                    token, 
                    self.jwt_secret, 
                    algorithms=["HS256"], 
                    options={"verify_aud": False}
                )
                return claims
            except Exception as e:
                logger.debug(f"Local HS256 JWT validation failed: {e}")

        # 3. Fallback to remote validation via Supabase Auth server API
        try:
            response = self.client.auth.get_user(token)
            if response and response.user:
                user = response.user
                return {
                    "sub": user.id,
                    "email": user.email,
                    "role": user.role or "authenticated",
                    "user_metadata": user.user_metadata,
                    "app_metadata": user.app_metadata
                }
        except Exception as e:
            logger.error(f"Remote Supabase Auth token validation failed: {e}")
            
        return None
