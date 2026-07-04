from jose import jwt
import time
from typing import Dict, Any, Optional

class LiveKitTokenGenerator:
    """
    Generates cryptographically signed JWT tokens for LiveKit video sessions
    using standard python-jose HS256 signatures.
    """
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def generate_token(
        self, 
        room_name: str, 
        participant_identity: str, 
        participant_name: Optional[str] = None,
        expiry_seconds: int = 7200
    ) -> str:
        now = int(time.time())
        claims = {
            "iss": self.api_key,
            "sub": participant_identity,
            "exp": now + expiry_seconds,
            "nbf": now,
            "video": {
                "roomJoin": True,
                "room": room_name,
                "roomCreate": True
            }
        }
        if participant_name:
            claims["name"] = participant_name
            
        # Sign JWT using LiveKit API Secret
        return jwt.encode(claims, self.api_secret, algorithm="HS256")
