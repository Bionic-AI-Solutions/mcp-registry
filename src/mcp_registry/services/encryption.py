"""Encryption service for tenant credentials."""

import json
import base64
from typing import Dict, Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from mcp_registry.config import get_settings

settings = get_settings()


class CredentialEncryption:
    """Handles encryption/decryption of tenant credentials."""
    
    def __init__(self):
        # In production, load from K8s secret via env var
        key = settings.credential_encryption_key.encode()
        self.fernet = Fernet(key)
    
    def encrypt(self, credentials: Dict[str, Any]) -> bytes:
        """Encrypt credential dict to bytes."""
        json_str = json.dumps(credentials)
        return self.fernet.encrypt(json_str.encode())
    
    def decrypt(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt bytes to credential dict."""
        decrypted = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key (for initial setup)."""
        return Fernet.generate_key().decode()


# Singleton instance
encryption_service = CredentialEncryption()
