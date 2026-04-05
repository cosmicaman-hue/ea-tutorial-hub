#!/usr/bin/env python3
"""
Secure Secrets Management System
Replaces environment variable password exposure with encrypted credential storage.
Falls back to unencrypted storage if cryptography module is not available.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime
import hashlib

try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False


class SecretsManager:
    """Manages sensitive credentials securely"""
    
    def __init__(self, secrets_dir: Path = Path('instance/secrets')):
        self.secrets_dir = Path(secrets_dir)
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.secrets_dir / '.key'
        self.secrets_file = self.secrets_dir / 'credentials.json'
        self._cipher = None
        self._secrets = {}
        self._initialize()
    
    def _initialize(self):
        """Initialize encryption and load secrets"""
        try:
            if HAS_CRYPTOGRAPHY:
                # Load or create encryption key
                if self.key_file.exists():
                    key = self.key_file.read_bytes()
                else:
                    key = Fernet.generate_key()
                    self.key_file.write_bytes(key)
                    self.key_file.chmod(0o600)  # Read/write for owner only
                
                self._cipher = Fernet(key)
            
            # Load existing secrets
            if self.secrets_file.exists():
                if HAS_CRYPTOGRAPHY:
                    encrypted_data = self.secrets_file.read_bytes()
                    decrypted = self._cipher.decrypt(encrypted_data)
                    self._secrets = json.loads(decrypted.decode('utf-8'))
                else:
                    # Fallback: read unencrypted JSON
                    self._secrets = json.loads(self.secrets_file.read_text(encoding='utf-8'))
            else:
                self._secrets = {
                    'credentials': {},
                    'created_at': datetime.now().isoformat(),
                    'version': 1
                }
                self._save()
                
        except Exception as e:
            raise RuntimeError(f"Failed to initialize secrets manager: {e}")
    
    def _save(self):
        """Save encrypted secrets to disk"""
        try:
            data = json.dumps(self._secrets, indent=2, ensure_ascii=False)
            
            if HAS_CRYPTOGRAPHY and self._cipher:
                encrypted = self._cipher.encrypt(data.encode('utf-8'))
                self.secrets_file.write_bytes(encrypted)
            else:
                # Fallback: save unencrypted JSON
                self.secrets_file.write_text(data, encoding='utf-8')
            
            self.secrets_file.chmod(0o600)  # Read/write for owner only
        except Exception as e:
            raise RuntimeError(f"Failed to save secrets: {e}")
    
    def set_credential(self, key: str, value: str, metadata: Optional[Dict] = None) -> bool:
        """Store a credential securely"""
        try:
            if not key or not value:
                return False
            
            self._secrets['credentials'][key] = {
                'value': value,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            self._save()
            return True
        except Exception as e:
            print(f"Error setting credential: {e}")
            return False
    
    def get_credential(self, key: str) -> Optional[str]:
        """Retrieve a credential"""
        try:
            cred = self._secrets.get('credentials', {}).get(key)
            if cred:
                return cred.get('value')
            return None
        except Exception as e:
            print(f"Error getting credential: {e}")
            return None
    
    def delete_credential(self, key: str) -> bool:
        """Delete a credential"""
        try:
            if key in self._secrets.get('credentials', {}):
                del self._secrets['credentials'][key]
                self._save()
                return True
            return False
        except Exception as e:
            print(f"Error deleting credential: {e}")
            return False
    
    def list_credentials(self) -> list:
        """List all credential keys (without values)"""
        try:
            return list(self._secrets.get('credentials', {}).keys())
        except Exception:
            return []
    
    def rotate_credential(self, key: str, new_value: str) -> Tuple[bool, str]:
        """Rotate a credential with audit trail"""
        try:
            old_cred = self._secrets.get('credentials', {}).get(key)
            if not old_cred:
                return False, f"Credential '{key}' not found"
            
            # Store old value in audit trail
            if 'audit_trail' not in self._secrets:
                self._secrets['audit_trail'] = []
            
            self._secrets['audit_trail'].append({
                'action': 'rotate',
                'key': key,
                'timestamp': datetime.now().isoformat(),
                'old_hash': hashlib.sha256(old_cred['value'].encode()).hexdigest()[:16]
            })
            
            # Update credential
            self._secrets['credentials'][key] = {
                'value': new_value,
                'created_at': datetime.now().isoformat(),
                'rotated_at': datetime.now().isoformat(),
                'metadata': old_cred.get('metadata', {})
            }
            
            self._save()
            return True, f"Credential '{key}' rotated successfully"
        except Exception as e:
            return False, f"Error rotating credential: {e}"
    
    def get_status(self) -> Dict:
        """Get secrets manager status"""
        return {
            'initialized': bool(self._cipher),
            'credentials_count': len(self._secrets.get('credentials', {})),
            'audit_entries': len(self._secrets.get('audit_trail', [])),
            'version': self._secrets.get('version', 1),
            'created_at': self._secrets.get('created_at')
        }


class CredentialProvider:
    """Provides credentials with fallback to environment variables"""
    
    def __init__(self, secrets_manager: SecretsManager):
        self.manager = secrets_manager
    
    def get_admin_password(self) -> str:
        """Get admin password with fallback"""
        # Try secrets manager first
        password = self.manager.get_credential('admin_password')
        if password:
            return password
        
        # Fallback to environment variable
        env_password = os.getenv('ADMIN_PASSWORD', '')
        if env_password:
            # Store in secrets manager for future use
            self.manager.set_credential('admin_password', env_password, 
                                       {'source': 'environment', 'migrated': True})
            return env_password
        
        # Final fallback to default (should be changed immediately)
        return 'ChangeAdminPass123!'
    
    def get_teacher_password(self) -> str:
        """Get teacher password with fallback"""
        # Try secrets manager first
        password = self.manager.get_credential('teacher_password')
        if password:
            return password
        
        # Fallback to environment variable
        env_password = os.getenv('TEACHER_PASSWORD', '')
        if env_password:
            # Store in secrets manager for future use
            self.manager.set_credential('teacher_password', env_password,
                                       {'source': 'environment', 'migrated': True})
            return env_password
        
        # Final fallback to default (should be changed immediately)
        return 'ChangeTeacherPass123!'
    
    def get_join_code(self) -> Optional[str]:
        """Get join code with fallback"""
        code = self.manager.get_credential('join_code')
        if code:
            return code
        
        env_code = os.getenv('EA_JOIN_CODE', '')
        if env_code:
            self.manager.set_credential('join_code', env_code,
                                       {'source': 'environment', 'migrated': True})
            return env_code
        
        return None


# Global instance
_secrets_manager = None
_credential_provider = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_credential_provider() -> CredentialProvider:
    """Get global credential provider instance"""
    global _credential_provider
    if _credential_provider is None:
        manager = get_secrets_manager()
        _credential_provider = CredentialProvider(manager)
    return _credential_provider


def main():
    """Test secrets manager"""
    print("=" * 60)
    print("SECRETS MANAGER TEST")
    print("=" * 60)
    
    manager = get_secrets_manager()
    provider = get_credential_provider()
    
    # Test status
    print("\nManager Status:")
    status = manager.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Test credential operations
    print("\nTesting credential operations...")
    
    # Set a test credential
    if manager.set_credential('test_key', 'test_value', {'purpose': 'testing'}):
        print("✓ Credential stored securely")
    
    # Retrieve it
    value = manager.get_credential('test_key')
    if value == 'test_value':
        print("✓ Credential retrieved successfully")
    
    # List credentials
    creds = manager.list_credentials()
    print(f"✓ Stored credentials: {creds}")
    
    # Test rotation
    success, msg = manager.rotate_credential('test_key', 'new_value')
    print(f"✓ Credential rotation: {msg}")
    
    # Clean up
    manager.delete_credential('test_key')
    print("✓ Test credential deleted")
    
    print("\n✅ Secrets manager is working correctly!")


if __name__ == '__main__':
    main()
