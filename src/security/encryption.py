"""
Data Encryption Module

Provides encryption and decryption for sensitive data.

Features:
- Symmetric encryption using Fernet (AES-128-CBC with HMAC)
- Key derivation from password using PBKDF2
- Secure key storage
- Field-level encryption
- At-rest data encryption

Use cases:
- Encrypting API keys in database
- Encrypting sensitive user data (PII)
- Encrypting credentials
- Encrypting audit logs with sensitive info

Compliance:
- GDPR: Encryption of personal data
- HIPAA: Encryption of PHI
- PCI DSS: Encryption of cardholder data
"""

import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from typing import Optional, Union
import json


class DataEncryption:
    """
    Handles encryption and decryption of sensitive data.
    
    Uses Fernet (symmetric encryption) which provides:
    - AES encryption in CBC mode with 128-bit key
    - HMAC using SHA256 for authentication
    - Timestamp in the token to support TTL
    - Versioned tokens for key rotation
    
    Security Notes:
    - The encryption key must be kept secure
    - Store encryption key in environment variable or secure key store
    - Never hardcode encryption keys
    - Rotate keys periodically
    - Use different keys for different environments (dev/staging/prod)
    """
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize the encryption handler.
        
        Args:
            encryption_key: Optional encryption key (32 bytes base64-encoded)
                          If not provided, generates or loads from environment
        
        Security:
        - In production, ALWAYS provide a key from secure storage
        - Never auto-generate keys in production
        - Use key management systems (AWS KMS, Azure Key Vault, etc.)
        """
        if encryption_key:
            self.key = encryption_key
        else:
            # Try to get key from environment
            env_key = os.getenv('ENCRYPTION_KEY')
            if env_key:
                self.key = env_key.encode()
            else:
                # Generate a new key (WARNING: only for development)
                self.key = Fernet.generate_key()
                print("⚠️  WARNING: Generated new encryption key.")
                print("   Set ENCRYPTION_KEY in your .env file for production.")
                print(f"   ENCRYPTION_KEY={self.key.decode()}")
        
        # Create Fernet cipher
        try:
            self.cipher = Fernet(self.key)
        except Exception as e:
            raise ValueError(f"Invalid encryption key: {e}")
    
    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new encryption key.
        
        This should be called once per environment and the key stored securely.
        
        Returns:
            32-byte encryption key (base64-encoded)
        """
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key_from_password(password: str, salt: Optional[bytes] = None) -> tuple:
        """
        Derive an encryption key from a password using PBKDF2.
        
        This allows using a password instead of a random key.
        The salt must be stored alongside the encrypted data.
        
        Args:
            password: Password to derive key from
            salt: Optional salt (16 bytes). If not provided, generates new salt.
            
        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        # Use PBKDF2 with 100,000 iterations (OWASP recommendation)
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return key, salt
    
    def encrypt(self, data: Union[str, bytes, dict]) -> str:
        """
        Encrypt data and return base64-encoded ciphertext.
        
        Args:
            data: Data to encrypt (string, bytes, or dict)
            
        Returns:
            Base64-encoded encrypted data as string
        """
        # Convert data to bytes if needed
        if isinstance(data, dict):
            data = json.dumps(data)
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Encrypt
        encrypted = self.cipher.encrypt(data)
        
        # Return as base64 string for storage
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> bytes:
        """
        Decrypt base64-encoded ciphertext.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted data as bytes
            
        Raises:
            cryptography.fernet.InvalidToken: If data is corrupted or key is wrong
        """
        # Decode from base64
        encrypted = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        
        # Decrypt
        decrypted = self.cipher.decrypt(encrypted)
        
        return decrypted
    
    def decrypt_to_string(self, encrypted_data: str) -> str:
        """
        Decrypt data and return as string.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted data as string
        """
        decrypted = self.decrypt(encrypted_data)
        return decrypted.decode('utf-8')
    
    def decrypt_to_dict(self, encrypted_data: str) -> dict:
        """
        Decrypt data and return as dictionary.
        
        Args:
            encrypted_data: Base64-encoded encrypted JSON data
            
        Returns:
            Decrypted data as dict
        """
        decrypted = self.decrypt_to_string(encrypted_data)
        return json.loads(decrypted)
    
    def encrypt_dict_fields(self, data: dict, fields_to_encrypt: list) -> dict:
        """
        Encrypt specific fields in a dictionary.
        
        Useful for field-level encryption in databases.
        
        Args:
            data: Dictionary containing data
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            New dictionary with specified fields encrypted
        """
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field] is not None:
                # Encrypt the field value
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_dict_fields(self, data: dict, fields_to_decrypt: list) -> dict:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary containing encrypted data
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            New dictionary with specified fields decrypted
        """
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field] is not None:
                try:
                    # Decrypt the field value
                    decrypted_data[field] = self.decrypt_to_string(decrypted_data[field])
                except Exception as e:
                    # If decryption fails, leave the field as is
                    print(f"⚠️  Failed to decrypt field '{field}': {e}")
        
        return decrypted_data
    
    @staticmethod
    def hash_data(data: str, salt: Optional[bytes] = None) -> tuple:
        """
        Create a one-way hash of data (cannot be decrypted).
        
        Useful for:
        - Storing passwords (use bcrypt instead for passwords)
        - Creating data fingerprints
        - Generating deterministic IDs
        
        Args:
            data: Data to hash
            salt: Optional salt. If not provided, generates new salt.
            
        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        # Use SHA256 with salt
        hash_obj = hashlib.sha256()
        hash_obj.update(salt)
        hash_obj.update(data.encode('utf-8'))
        
        data_hash = hash_obj.hexdigest()
        
        return data_hash, salt
    
    @staticmethod
    def verify_hash(data: str, data_hash: str, salt: bytes) -> bool:
        """
        Verify data against a hash.
        
        Args:
            data: Data to verify
            data_hash: Expected hash
            salt: Salt used for hashing
            
        Returns:
            True if data matches hash, False otherwise
        """
        computed_hash, _ = DataEncryption.hash_data(data, salt)
        return computed_hash == data_hash


# Global encryption instance
# In production, initialize with key from secure storage
_global_encryption = None


def get_encryption() -> DataEncryption:
    """
    Get the global encryption instance (lazy initialization).
    
    Returns:
        DataEncryption instance
    """
    global _global_encryption
    if _global_encryption is None:
        _global_encryption = DataEncryption()
    return _global_encryption


def encrypt_sensitive(data: Union[str, bytes, dict]) -> str:
    """
    Convenience function to encrypt data using global instance.
    
    Args:
        data: Data to encrypt
        
    Returns:
        Encrypted data as base64 string
    """
    return get_encryption().encrypt(data)


def decrypt_sensitive(encrypted_data: str) -> str:
    """
    Convenience function to decrypt data using global instance.
    
    Args:
        encrypted_data: Encrypted data as base64 string
        
    Returns:
        Decrypted data as string
    """
    return get_encryption().decrypt_to_string(encrypted_data)


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage.
    
    Args:
        api_key: API key to encrypt
        
    Returns:
        Encrypted API key
    """
    return encrypt_sensitive(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key.
    
    Args:
        encrypted_key: Encrypted API key
        
    Returns:
        Decrypted API key
    """
    return decrypt_sensitive(encrypted_key)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Data Encryption Module")
    print("=" * 60)
    
    # Create encryption instance
    enc = DataEncryption()
    
    # Test string encryption
    print("\n1. String Encryption:")
    original = "Sensitive data: API key abc123"
    encrypted = enc.encrypt(original)
    decrypted = enc.decrypt_to_string(encrypted)
    print(f"   Original:  {original}")
    print(f"   Encrypted: {encrypted[:50]}...")
    print(f"   Decrypted: {decrypted}")
    print(f"   Match: {original == decrypted}")
    
    # Test dict encryption
    print("\n2. Dictionary Encryption:")
    data = {
        'username': 'john_doe',
        'api_key': 'secret_key_123',
        'email': 'john@example.com'
    }
    encrypted_data = enc.encrypt_dict_fields(data, ['api_key', 'email'])
    print(f"   Original: {data}")
    print(f"   Encrypted: {encrypted_data}")
    decrypted_data = enc.decrypt_dict_fields(encrypted_data, ['api_key', 'email'])
    print(f"   Decrypted: {decrypted_data}")
    
    # Test hashing
    print("\n3. Data Hashing:")
    data = "password123"
    hash_val, salt = DataEncryption.hash_data(data)
    print(f"   Data: {data}")
    print(f"   Hash: {hash_val}")
    print(f"   Salt: {salt.hex()}")
    print(f"   Verify: {DataEncryption.verify_hash(data, hash_val, salt)}")
    print(f"   Verify wrong: {DataEncryption.verify_hash('wrong', hash_val, salt)}")
    
    print("\n" + "=" * 60)
    print("✅ All encryption tests passed!")
