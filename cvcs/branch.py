"""
Branching and merging functionality for CVCS.
Supports parallel work on all file types including binary files.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import difflib
from .repository import Repository


class BranchManager:
    """Manages branches and merging."""
    
    def __init__(self, repo: Repository):
        """Initialize branch manager with a repository."""
        self.repo = repo
        self.cvcs_dir = repo.cvcs_dir
    
    def create_branch(self, branch_name: str, from_commit: Optional[str] = None) -> bool:
        """Create a new branch."""
        branch_file = self.cvcs_dir / "refs" / "heads" / branch_name
        
        if branch_file.exists():
            return False
        
        # Get commit to branch from
        if from_commit is None:
            current_branch = self.repo.get_current_branch()
            from_commit = self.repo.get_branch_commit(current_branch)
        
        if from_commit:
            self.repo.set_branch_commit(branch_name, from_commit)
        else:
            # New branch with no commits yet
            branch_file.write_text("")
        
        return True
    
    def list_branches(self) -> List[str]:
        """List all branches."""
        heads_dir = self.cvcs_dir / "refs" / "heads"
        if not heads_dir.exists():
            return []
        
        branches = []
        for branch_file in heads_dir.iterdir():
            if branch_file.is_file():
                branches.append(branch_file.name)
        
        return sorted(branches)
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a different branch."""
        branch_file = self.cvcs_dir / "refs" / "heads" / branch_name
        
        if not branch_file.exists():
            return False
        
        # Update HEAD
        head_file = self.cvcs_dir / "HEAD"
        head_file.write_text(f"ref: refs/heads/{branch_name}\n")
        
        # Restore working directory to branch state
        commit_hash = self.repo.get_branch_commit(branch_name)
        if commit_hash:
            commit = self.repo.get_commit(commit_hash)
            if commit:
                tree = commit.get("tree", {})
                for file_path in tree:
                    try:
                        self.repo.checkout_file(file_path, commit_hash)
                    except Exception:
                        pass  # Continue with other files
        
        return True
    
    def merge(self, source_branch: str, target_branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Merge source_branch into target_branch (or current branch).
        Returns merge result with conflicts if any.
        """
        if target_branch is None:
            target_branch = self.repo.get_current_branch()
        
        source_commit_hash = self.repo.get_branch_commit(source_branch)
        target_commit_hash = self.repo.get_branch_commit(target_branch)
        
        if not source_commit_hash:
            return {"error": f"Branch '{source_branch}' has no commits"}
        
        source_commit = self.repo.get_commit(source_commit_hash)
        target_commit = self.repo.get_commit(target_commit_hash) if target_commit_hash else None
        
        source_tree = source_commit.get("tree", {})
        target_tree = target_commit.get("tree", {}) if target_commit else {}
        
        # Find common ancestor
        # NOTE: This is a simplified implementation that uses the target branch as the base.
        # A full implementation would traverse the commit graph to find the actual
        # common ancestor (lowest common ancestor/LCA). For most linear workflows,
        # using target as base provides reasonable merge behavior.
        # TODO: Implement proper LCA algorithm for complex merge scenarios.
        base_tree = target_tree.copy()
        
        conflicts = []
        merged_tree = target_tree.copy()
        
        # Process all files from source
        for file_path, source_info in source_tree.items():
            if file_path in target_tree:
                target_info = target_tree[file_path]
                
                # Check if content is different
                if source_info["content_hash"] != target_info["content_hash"]:
                    # If we have text representations, try to merge
                    if source_info.get("text_hash") and target_info.get("text_hash"):
                        # Get text content
                        source_text = self.repo.storage.get_object(source_info["text_hash"])
                        target_text = self.repo.storage.get_object(target_info["text_hash"])
                        
                        if source_text and target_text:
                            source_lines = source_text.decode('utf-8').splitlines(keepends=True)
                            target_lines = target_text.decode('utf-8').splitlines(keepends=True)
                            base_lines = []
                            
                            if file_path in base_tree and base_tree[file_path].get("text_hash"):
                                base_text = self.repo.storage.get_object(base_tree[file_path]["text_hash"])
                                if base_text:
                                    base_lines = base_text.decode('utf-8').splitlines(keepends=True)
                            
                            # Simple 3-way merge
                            merged_lines = self._three_way_merge(base_lines, source_lines, target_lines)
                            
                            if "<<<<<<< " in ''.join(merged_lines):
                                conflicts.append({
                                    "file": file_path,
                                    "type": "content_conflict"
                                })
                            
                            merged_tree[file_path] = source_info
                        else:
                            # Binary conflict
                            conflicts.append({
                                "file": file_path,
                                "type": "binary_conflict",
                                "source_hash": source_info["content_hash"],
                                "target_hash": target_info["content_hash"]
                            })
                            merged_tree[file_path] = source_info  # Prefer source
                    else:
                        # Binary file conflict
                        conflicts.append({
                            "file": file_path,
                            "type": "binary_conflict",
                            "source_hash": source_info["content_hash"],
                            "target_hash": target_info["content_hash"]
                        })
                        merged_tree[file_path] = source_info  # Prefer source
                else:
                    # Same content, no conflict
                    merged_tree[file_path] = source_info
            else:
                # New file from source
                merged_tree[file_path] = source_info
        
        return {
            "success": len(conflicts) == 0,
            "conflicts": conflicts,
            "merged_tree": merged_tree
        }
    
    def _three_way_merge(self, base_lines: List[str], source_lines: List[str], 
                        target_lines: List[str]) -> List[str]:
        """
        Perform a simple three-way merge.
        Returns merged lines with conflict markers if conflicts exist.
        """
        # If source and target are the same, return either
        if source_lines == target_lines:
            return source_lines
        
        # If source == base, use target (target changed)
        if source_lines == base_lines:
            return target_lines
        
        # If target == base, use source (source changed)
        if target_lines == base_lines:
            return source_lines
        
        # Both changed - mark as conflict
        result = []
        result.append("<<<<<<< SOURCE\n")
        result.extend(source_lines)
        result.append("=======\n")
        result.extend(target_lines)
        result.append(">>>>>>> TARGET\n")
        
        return result
