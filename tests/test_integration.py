"""
Integration tests for CVCS repository operations.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from cvcs.repository import Repository
from cvcs.branch import BranchManager


class TestRepositoryIntegration(unittest.TestCase):
    """Integration tests for repository operations."""
    
    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.repo = Repository(self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_init_repository(self):
        """Test repository initialization."""
        result = self.repo.init()
        self.assertTrue(result)
        
        # Check that necessary files/dirs were created
        self.assertTrue((Path(self.test_dir) / ".cvcs").exists())
        self.assertTrue((Path(self.test_dir) / ".cvcs" / "objects").exists())
        self.assertTrue((Path(self.test_dir) / ".cvcs" / "refs" / "heads").exists())
        self.assertTrue((Path(self.test_dir) / ".cvcs" / "HEAD").exists())
        self.assertTrue((Path(self.test_dir) / ".cvcs" / "index").exists())
        
        # Check HEAD points to main
        head_content = (Path(self.test_dir) / ".cvcs" / "HEAD").read_text()
        self.assertIn("main", head_content)
    
    def test_add_and_commit_workflow(self):
        """Test complete add and commit workflow."""
        self.repo.init()
        
        # Create a test file
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello, CVCS!")
        
        # Add file
        self.repo.add_file("test.txt")
        
        # Commit
        commit_hash = self.repo.commit("Initial commit", "Test User")
        self.assertIsNotNone(commit_hash)
        self.assertEqual(len(commit_hash), 64)
        
        # Verify commit exists
        commit = self.repo.get_commit(commit_hash)
        self.assertIsNotNone(commit)
        self.assertEqual(commit["message"], "Initial commit")
        self.assertEqual(commit["author"], "Test User")
        self.assertIn("test.txt", commit["tree"])
    
    def test_log(self):
        """Test commit log retrieval."""
        self.repo.init()
        
        # Create and commit multiple files
        for i in range(3):
            test_file = Path(self.test_dir) / f"test{i}.txt"
            test_file.write_text(f"Content {i}")
            self.repo.add_file(f"test{i}.txt")
            self.repo.commit(f"Commit {i}", "Test User")
        
        # Get log
        log = self.repo.log(max_count=10)
        self.assertEqual(len(log), 3)
        
        # Commits should be in reverse chronological order
        self.assertEqual(log[0]["message"], "Commit 2")
        self.assertEqual(log[1]["message"], "Commit 1")
        self.assertEqual(log[2]["message"], "Commit 0")
    
    def test_branch_creation_and_switching(self):
        """Test branch creation and switching."""
        self.repo.init()
        branch_mgr = BranchManager(self.repo)
        
        # Create test file and commit
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Initial content")
        self.repo.add_file("test.txt")
        self.repo.commit("Initial commit", "Test User")
        
        # Create branch
        result = branch_mgr.create_branch("feature")
        self.assertTrue(result)
        
        # List branches
        branches = branch_mgr.list_branches()
        self.assertIn("main", branches)
        self.assertIn("feature", branches)
        
        # Switch branch
        result = branch_mgr.switch_branch("feature")
        self.assertTrue(result)
        
        # Verify current branch
        current = self.repo.get_current_branch()
        self.assertEqual(current, "feature")
    
    def test_merge_without_conflicts(self):
        """Test merging branches without conflicts."""
        self.repo.init()
        branch_mgr = BranchManager(self.repo)
        
        # Create initial commit
        file1 = Path(self.test_dir) / "file1.txt"
        file1.write_text("File 1 content")
        self.repo.add_file("file1.txt")
        self.repo.commit("Initial commit", "Test User")
        
        # Create and switch to feature branch
        branch_mgr.create_branch("feature")
        branch_mgr.switch_branch("feature")
        
        # Add new file in feature branch
        file2 = Path(self.test_dir) / "file2.txt"
        file2.write_text("File 2 content")
        self.repo.add_file("file2.txt")
        self.repo.commit("Add file2", "Test User")
        
        # Switch back to main
        branch_mgr.switch_branch("main")
        
        # Merge feature into main
        result = branch_mgr.merge("feature")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["conflicts"]), 0)
    
    def test_checkout_file(self):
        """Test checking out a file from a commit."""
        self.repo.init()
        
        # Create and commit file
        test_file = Path(self.test_dir) / "test.txt"
        original_content = "Original content"
        test_file.write_text(original_content)
        self.repo.add_file("test.txt")
        self.repo.commit("Initial commit", "Test User")
        
        # Modify file
        test_file.write_text("Modified content")
        
        # Checkout from HEAD
        self.repo.checkout_file("test.txt")
        
        # Verify content restored
        restored_content = test_file.read_text()
        self.assertEqual(restored_content, original_content)


if __name__ == '__main__':
    unittest.main()
