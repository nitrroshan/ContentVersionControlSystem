"""
Storage module for content-addressable storage.
Uses SHA-256 hashing to store file content uniquely.
"""

import hashlib
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class ContentStorage:
    """Manages content-addressable storage for files."""
    
    def __init__(self, repo_path: str):
        """Initialize storage in the given repository path."""
        self.repo_path = Path(repo_path)
        self.objects_dir = self.repo_path / ".cvcs" / "objects"
        self.refs_dir = self.repo_path / ".cvcs" / "refs"
        self.refs_dir.mkdir(parents=True, exist_ok=True)
        self.objects_dir.mkdir(parents=True, exist_ok=True)
    
    def hash_content(self, content: bytes) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(content).hexdigest()
    
    def store_object(self, content: bytes) -> str:
        """
        Store content in object database.
        Returns the hash of the stored content.
        """
        content_hash = self.hash_content(content)
        hash_prefix = content_hash[:2]
        hash_suffix = content_hash[2:]
        
        obj_dir = self.objects_dir / hash_prefix
        obj_dir.mkdir(exist_ok=True)
        
        obj_path = obj_dir / hash_suffix
        if not obj_path.exists():
            with open(obj_path, 'wb') as f:
                f.write(content)
        
        return content_hash
    
    def get_object(self, content_hash: str) -> Optional[bytes]:
        """Retrieve content by its hash."""
        hash_prefix = content_hash[:2]
        hash_suffix = content_hash[2:]
        
        obj_path = self.objects_dir / hash_prefix / hash_suffix
        if obj_path.exists():
            with open(obj_path, 'rb') as f:
                return f.read()
        return None
    
    def store_metadata(self, metadata: Dict[str, Any], metadata_id: str) -> str:
        """Store metadata as JSON."""
        content = json.dumps(metadata, indent=2).encode('utf-8')
        return self.store_object(content)
    
    def get_metadata(self, metadata_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata by hash."""
        content = self.get_object(metadata_hash)
        if content:
            return json.loads(content.decode('utf-8'))
        return None
