from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import json
from typing import Any, Dict

class EncryptionManager:
    """Manages encryption/decryption for user data"""
    
    def __init__(self, user_id: int, master_key: str = None):
        self.user_id = user_id
        self.master_key = master_key or os.getenv("ENCRYPTION_KEY")
        if not self.master_key:
            raise ValueError("ENCRYPTION_KEY must be set in environment or provided")
        self._fernet = None
    
    def _get_fernet(self) -> Fernet:
        """Get or create Fernet instance for this user"""
        if self._fernet is None:
            # Derive user-specific key from master key + user_id
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=f"mailmind_user_{self.user_id}".encode(),
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, data: str | Dict[str, Any]) -> str:
        """Encrypt string or dict data"""
        if isinstance(data, dict):
            data = json.dumps(data)
        return self._get_fernet().encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data to string"""
        return self._get_fernet().decrypt(encrypted_data.encode()).decode()
    
    def decrypt_json(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt and parse JSON data"""
        return json.loads(self.decrypt(encrypted_data))

def generate_master_key() -> str:
    """Generate a new master encryption key"""
    return Fernet.generate_key().decode()

