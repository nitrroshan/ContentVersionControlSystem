"""
Unit tests for CVCS storage module.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from cvcs.storage import ContentStorage


class TestContentStorage(unittest.TestCase):
    """Test ContentStorage functionality."""
    
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.storage = ContentStorage(self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test storage initialization creates necessary directories."""
        self.assertTrue((Path(self.test_dir) / ".cvcs" / "objects").exists())
        self.assertTrue((Path(self.test_dir) / ".cvcs" / "refs").exists())
    
    def test_hash_content(self):
        """Test content hashing."""
        content = b"Hello, World!"
        hash1 = self.storage.hash_content(content)
        hash2 = self.storage.hash_content(content)
        
        # Same content should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Different content should produce different hash
        different_content = b"Different content"
        hash3 = self.storage.hash_content(different_content)
        self.assertNotEqual(hash1, hash3)
    
    def test_store_and_retrieve_object(self):
        """Test storing and retrieving objects."""
        content = b"Test content for storage"
        
        # Store object
        content_hash = self.storage.store_object(content)
        self.assertIsNotNone(content_hash)
        self.assertEqual(len(content_hash), 64)  # SHA-256 produces 64 hex chars
        
        # Retrieve object
        retrieved = self.storage.get_object(content_hash)
        self.assertEqual(content, retrieved)
    
    def test_store_duplicate_content(self):
        """Test that duplicate content is not stored twice."""
        content = b"Duplicate test content"
        
        # Store same content twice
        hash1 = self.storage.store_object(content)
        hash2 = self.storage.store_object(content)
        
        # Should produce same hash
        self.assertEqual(hash1, hash2)
        
        # Should be retrievable
        retrieved = self.storage.get_object(hash1)
        self.assertEqual(content, retrieved)
    
    def test_get_nonexistent_object(self):
        """Test retrieving non-existent object returns None."""
        fake_hash = "0" * 64
        result = self.storage.get_object(fake_hash)
        self.assertIsNone(result)
    
    def test_store_and_retrieve_metadata(self):
        """Test storing and retrieving metadata."""
        metadata = {
            "type": "commit",
            "message": "Test commit",
            "author": "Test Author",
            "timestamp": 123456789
        }
        
        # Store metadata
        metadata_hash = self.storage.store_metadata(metadata, "test")
        self.assertIsNotNone(metadata_hash)
        
        # Retrieve metadata
        retrieved = self.storage.get_metadata(metadata_hash)
        self.assertEqual(metadata, retrieved)


if __name__ == '__main__':
    unittest.main()
