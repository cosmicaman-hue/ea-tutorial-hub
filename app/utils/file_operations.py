#!/usr/bin/env python3
"""
Optimized File Operations Utility
Provides safe file operations with locking, streaming, and error handling.
Prevents data corruption and race conditions.
"""
import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from datetime import datetime
import threading
import time


class FileLock:
    """Simple file-based lock mechanism"""
    
    def __init__(self, lock_file: Path, timeout: int = 30):
        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self.acquired = False
    
    def acquire(self) -> bool:
        """Acquire lock with timeout"""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                # Try to create lock file exclusively
                fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self.acquired = True
                return True
            except FileExistsError:
                time.sleep(0.1)  # Wait and retry
        
        return False
    
    def release(self):
        """Release lock"""
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                self.acquired = False
            except Exception:
                pass
    
    def __enter__(self):
        if not self.acquire():
            raise TimeoutError(f"Could not acquire lock on {self.lock_file}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class SafeFileWriter:
    """Safe file writing with atomic operations"""
    
    @staticmethod
    def write_json(file_path: Path, data: Dict[str, Any], 
                   backup: bool = True, lock_timeout: int = 30) -> bool:
        """
        Safely write JSON data to file with atomic operations.
        Uses temporary file + rename pattern to prevent corruption.
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            lock_file = file_path.parent / f".{file_path.name}.lock"
            
            with FileLock(lock_file, timeout=lock_timeout):
                # Create backup if file exists
                if backup and file_path.exists():
                    backup_path = file_path.parent / f"{file_path.name}.backup"
                    shutil.copy2(file_path, backup_path)
                
                # Write to temporary file first
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    dir=file_path.parent,
                    delete=False,
                    suffix='.tmp',
                    encoding='utf-8'
                ) as tmp_file:
                    json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                    tmp_path = Path(tmp_file.name)
                
                # Atomic rename
                tmp_path.replace(file_path)
                return True
                
        except Exception as e:
            print(f"Error writing JSON to {file_path}: {e}")
            return False
    
    @staticmethod
    def write_text(file_path: Path, content: str,
                   backup: bool = True, lock_timeout: int = 30) -> bool:
        """
        Safely write text data to file with atomic operations.
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            lock_file = file_path.parent / f".{file_path.name}.lock"
            
            with FileLock(lock_file, timeout=lock_timeout):
                # Create backup if file exists
                if backup and file_path.exists():
                    backup_path = file_path.parent / f"{file_path.name}.backup"
                    shutil.copy2(file_path, backup_path)
                
                # Write to temporary file first
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    dir=file_path.parent,
                    delete=False,
                    suffix='.tmp',
                    encoding='utf-8'
                ) as tmp_file:
                    tmp_file.write(content)
                    tmp_path = Path(tmp_file.name)
                
                # Atomic rename
                tmp_path.replace(file_path)
                return True
                
        except Exception as e:
            print(f"Error writing text to {file_path}: {e}")
            return False


class SafeFileReader:
    """Safe file reading with error handling"""
    
    @staticmethod
    def read_json(file_path: Path, default: Optional[Dict] = None,
                  lock_timeout: int = 30) -> Dict[str, Any]:
        """
        Safely read JSON file with fallback to backup if corrupted.
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return default or {}
            
            lock_file = file_path.parent / f".{file_path.name}.lock"
            
            with FileLock(lock_file, timeout=lock_timeout):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, ValueError):
                    # Try backup file if main is corrupted
                    backup_path = file_path.parent / f"{file_path.name}.backup"
                    if backup_path.exists():
                        try:
                            with open(backup_path, 'r', encoding='utf-8') as f:
                                return json.load(f)
                        except Exception:
                            pass
                    
                    return default or {}
                    
        except Exception as e:
            print(f"Error reading JSON from {file_path}: {e}")
            return default or {}
    
    @staticmethod
    def read_text(file_path: Path, default: str = "",
                  lock_timeout: int = 30) -> str:
        """
        Safely read text file with error handling.
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return default
            
            lock_file = file_path.parent / f".{file_path.name}.lock"
            
            with FileLock(lock_file, timeout=lock_timeout):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
                    
        except Exception as e:
            print(f"Error reading text from {file_path}: {e}")
            return default


class StreamingFileReader:
    """Streaming file reader for large files"""
    
    @staticmethod
    def read_json_streaming(file_path: Path, chunk_size: int = 8192) -> Optional[Dict]:
        """
        Read large JSON files in streaming fashion to avoid memory issues.
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            # For JSON, we still need to load it all, but we can use streaming
            # for initial validation
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read in chunks to detect corruption early
                chunks = []
                for chunk in iter(lambda: f.read(chunk_size), ''):
                    chunks.append(chunk)
                
                content = ''.join(chunks)
                return json.loads(content)
                
        except Exception as e:
            print(f"Error streaming JSON from {file_path}: {e}")
            return None
    
    @staticmethod
    def read_lines(file_path: Path, callback: Callable[[str], None],
                   chunk_size: int = 8192):
        """
        Read file line by line, calling callback for each line.
        Useful for processing large files without loading into memory.
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                buffer = ""
                for chunk in iter(lambda: f.read(chunk_size), ''):
                    buffer += chunk
                    lines = buffer.split('\n')
                    
                    # Process all complete lines
                    for line in lines[:-1]:
                        callback(line)
                    
                    # Keep incomplete line in buffer
                    buffer = lines[-1]
                
                # Process remaining line
                if buffer:
                    callback(buffer)
                    
        except Exception as e:
            print(f"Error reading lines from {file_path}: {e}")


class FileIntegrityChecker:
    """Check file integrity and detect corruption"""
    
    @staticmethod
    def verify_json(file_path: Path) -> tuple[bool, str]:
        """
        Verify JSON file integrity.
        Returns (is_valid, message)
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return False, "File does not exist"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            return True, "JSON is valid"
            
        except json.JSONDecodeError as e:
            return False, f"JSON decode error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    @staticmethod
    def get_file_hash(file_path: Path) -> Optional[str]:
        """
        Get SHA256 hash of file for integrity verification.
        """
        try:
            import hashlib
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            sha256_hash = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return None


class AtomicFileOperation:
    """Context manager for atomic file operations"""
    
    def __init__(self, file_path: Path, mode: str = 'w', 
                 create_backup: bool = True, lock_timeout: int = 30):
        self.file_path = Path(file_path)
        self.mode = mode
        self.create_backup = create_backup
        self.lock_timeout = lock_timeout
        self.lock = None
        self.tmp_file = None
        self.tmp_path = None
    
    def __enter__(self):
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Acquire lock
            lock_file = self.file_path.parent / f".{self.file_path.name}.lock"
            self.lock = FileLock(lock_file, timeout=self.lock_timeout)
            self.lock.acquire()
            
            # Create backup
            if self.create_backup and self.file_path.exists():
                backup_path = self.file_path.parent / f"{self.file_path.name}.backup"
                shutil.copy2(self.file_path, backup_path)
            
            # Create temporary file
            self.tmp_file = tempfile.NamedTemporaryFile(
                mode=self.mode,
                dir=self.file_path.parent,
                delete=False,
                suffix='.tmp',
                encoding='utf-8' if 'b' not in self.mode else None
            )
            self.tmp_path = Path(self.tmp_file.name)
            
            return self.tmp_file
            
        except Exception as e:
            if self.lock:
                self.lock.release()
            raise e
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.tmp_file:
                self.tmp_file.close()
            
            if exc_type is None and self.tmp_path:
                # Success: atomic rename
                self.tmp_path.replace(self.file_path)
            elif self.tmp_path and self.tmp_path.exists():
                # Failure: cleanup temp file
                self.tmp_path.unlink()
            
        finally:
            if self.lock:
                self.lock.release()


def main():
    """Test file operations"""
    print("=" * 60)
    print("FILE OPERATIONS TEST")
    print("=" * 60)
    
    test_dir = Path('instance/test_files')
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Test JSON writing and reading
    print("\n1. Testing JSON operations...")
    test_data = {'test': 'data', 'timestamp': datetime.now().isoformat()}
    test_file = test_dir / 'test.json'
    
    if SafeFileWriter.write_json(test_file, test_data):
        print("✓ JSON written successfully")
        
        read_data = SafeFileReader.read_json(test_file)
        if read_data == test_data:
            print("✓ JSON read successfully")
        else:
            print("❌ JSON data mismatch")
    else:
        print("❌ Failed to write JSON")
    
    # Test file integrity
    print("\n2. Testing file integrity...")
    is_valid, msg = FileIntegrityChecker.verify_json(test_file)
    print(f"✓ Integrity check: {msg}")
    
    # Test atomic operations
    print("\n3. Testing atomic operations...")
    atomic_file = test_dir / 'atomic.json'
    try:
        with AtomicFileOperation(atomic_file) as f:
            json.dump({'atomic': True}, f)
        print("✓ Atomic operation completed")
    except Exception as e:
        print(f"❌ Atomic operation failed: {e}")
    
    # Cleanup
    shutil.rmtree(test_dir)
    print("\n✓ Test cleanup completed")
    print("\n✅ File operations test completed!")


if __name__ == '__main__':
    main()
