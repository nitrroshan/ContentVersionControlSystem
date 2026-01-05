"""
Repository management for CVCS.
Handles initialization, commits, and version tracking.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from .storage import ContentStorage
from .content_extractor import ContentExtractor


class Repository:
    """Manages a CVCS repository."""
    
    def __init__(self, repo_path: str = "."):
        """Initialize repository object."""
        self.repo_path = Path(repo_path).resolve()
        self.cvcs_dir = self.repo_path / ".cvcs"
        self.storage = None
        
        if self.cvcs_dir.exists():
            self.storage = ContentStorage(str(self.repo_path))
    
    def init(self) -> bool:
        """Initialize a new CVCS repository."""
        if self.cvcs_dir.exists():
            print(f"Repository already exists at {self.cvcs_dir}")
            return False
        
        # Create directory structure
        self.cvcs_dir.mkdir(parents=True)
        (self.cvcs_dir / "objects").mkdir()
        (self.cvcs_dir / "refs" / "heads").mkdir(parents=True)
        (self.cvcs_dir / "refs" / "tags").mkdir(parents=True)
        
        # Initialize storage
        self.storage = ContentStorage(str(self.repo_path))
        
        # Create initial HEAD pointing to main branch
        head_file = self.cvcs_dir / "HEAD"
        head_file.write_text("ref: refs/heads/main\n")
        
        # Create index (staging area)
        index_file = self.cvcs_dir / "index"
        index_file.write_text(json.dumps({}))
        
        # Create config
        config = {
            "version": "1",
            "core": {
                "repositoryformatversion": 1
            }
        }
        config_file = self.cvcs_dir / "config"
        config_file.write_text(json.dumps(config, indent=2))
        
        return True
    
    def get_current_branch(self) -> str:
        """Get the name of the current branch."""
        head_file = self.cvcs_dir / "HEAD"
        if not head_file.exists():
            return "main"
        
        head_content = head_file.read_text().strip()
        if head_content.startswith("ref: refs/heads/"):
            return head_content.replace("ref: refs/heads/", "")
        return "main"
    
    def get_branch_commit(self, branch_name: str) -> Optional[str]:
        """Get the commit hash for a branch."""
        branch_file = self.cvcs_dir / "refs" / "heads" / branch_name
        if branch_file.exists():
            return branch_file.read_text().strip()
        return None
    
    def set_branch_commit(self, branch_name: str, commit_hash: str):
        """Set the commit hash for a branch."""
        branch_file = self.cvcs_dir / "refs" / "heads" / branch_name
        branch_file.parent.mkdir(parents=True, exist_ok=True)
        branch_file.write_text(commit_hash)
    
    def add_file(self, file_path: str):
        """Add a file to the staging area."""
        if not self.storage:
            raise RuntimeError("Not a CVCS repository")
        
        full_path = self.repo_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract and store content
        raw_content, text_content = ContentExtractor.extract_content(str(full_path))
        content_hash = self.storage.store_object(raw_content)
        
        # Store text representation if available
        text_hash = None
        if text_content:
            text_hash = self.storage.store_object(text_content.encode('utf-8'))
        
        # Update index
        index_file = self.cvcs_dir / "index"
        index = json.loads(index_file.read_text())
        
        index[file_path] = {
            "content_hash": content_hash,
            "text_hash": text_hash,
            "size": len(raw_content)
        }
        
        index_file.write_text(json.dumps(index, indent=2))
    
    def commit(self, message: str, author: str = "CVCS User") -> str:
        """Create a commit from the staging area."""
        if not self.storage:
            raise RuntimeError("Not a CVCS repository")
        
        # Read index
        index_file = self.cvcs_dir / "index"
        index = json.loads(index_file.read_text())
        
        if not index:
            raise RuntimeError("Nothing to commit")
        
        # Get current branch and parent commit
        current_branch = self.get_current_branch()
        parent_commit = self.get_branch_commit(current_branch)
        
        # Create commit object
        commit_data = {
            "type": "commit",
            "tree": index.copy(),
            "parent": parent_commit,
            "message": message,
            "author": author,
            "timestamp": time.time()
        }
        
        # Store commit
        commit_hash = self.storage.store_metadata(commit_data, "commit")
        
        # Update branch reference
        self.set_branch_commit(current_branch, commit_hash)
        
        # Clear index
        index_file.write_text(json.dumps({}))
        
        return commit_hash
    
    def get_commit(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve a commit by hash."""
        if not self.storage:
            return None
        return self.storage.get_metadata(commit_hash)
    
    def log(self, branch_name: Optional[str] = None, max_count: int = 10) -> List[Dict[str, Any]]:
        """Get commit history for a branch."""
        if not self.storage:
            return []
        
        if branch_name is None:
            branch_name = self.get_current_branch()
        
        commit_hash = self.get_branch_commit(branch_name)
        commits = []
        
        while commit_hash and len(commits) < max_count:
            commit = self.get_commit(commit_hash)
            if not commit:
                break
            
            commits.append({
                "hash": commit_hash,
                "message": commit.get("message", ""),
                "author": commit.get("author", ""),
                "timestamp": commit.get("timestamp", 0)
            })
            
            commit_hash = commit.get("parent")
        
        return commits
    
    def checkout_file(self, file_path: str, commit_hash: Optional[str] = None):
        """Restore a file from a commit."""
        if not self.storage:
            raise RuntimeError("Not a CVCS repository")
        
        # If no commit specified, use current branch HEAD
        if commit_hash is None:
            current_branch = self.get_current_branch()
            commit_hash = self.get_branch_commit(current_branch)
        
        if not commit_hash:
            raise RuntimeError("No commit found")
        
        commit = self.get_commit(commit_hash)
        if not commit:
            raise RuntimeError(f"Commit not found: {commit_hash}")
        
        tree = commit.get("tree", {})
        if file_path not in tree:
            raise FileNotFoundError(f"File not in commit: {file_path}")
        
        file_info = tree[file_path]
        content = self.storage.get_object(file_info["content_hash"])
        
        if content:
            full_path = self.repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(content)
