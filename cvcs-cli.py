#!/usr/bin/env python3
"""
CVCS Command Line Interface
Content Version Control System for all file types
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from cvcs.repository import Repository
from cvcs.branch import BranchManager


def cmd_init(args):
    """Initialize a new CVCS repository."""
    repo = Repository(args.path)
    if repo.init():
        print(f"Initialized empty CVCS repository in {repo.cvcs_dir}/")
        return 0
    else:
        print(f"Error: Repository already exists in {repo.cvcs_dir}/")
        return 1


def cmd_add(args):
    """Add files to staging area."""
    repo = Repository(args.path)
    if not repo.storage:
        print("Error: Not a CVCS repository. Run 'cvcs init' first.")
        return 1
    
    for file_path in args.files:
        try:
            repo.add_file(file_path)
            print(f"Added '{file_path}' to staging area")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
        except Exception as e:
            print(f"Error adding '{file_path}': {e}")
            return 1
    
    return 0


def cmd_commit(args):
    """Create a commit from staged files."""
    repo = Repository(args.path)
    if not repo.storage:
        print("Error: Not a CVCS repository. Run 'cvcs init' first.")
        return 1
    
    if not args.message:
        print("Error: Commit message is required. Use -m 'message'")
        return 1
    
    try:
        commit_hash = repo.commit(args.message, args.author)
        branch = repo.get_current_branch()
        print(f"[{branch} {commit_hash[:7]}] {args.message}")
        return 0
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error creating commit: {e}")
        return 1


def cmd_log(args):
    """Show commit history."""
    repo = Repository(args.path)
    if not repo.storage:
        print("Error: Not a CVCS repository. Run 'cvcs init' first.")
        return 1
    
    commits = repo.log(args.branch, args.max_count)
    
    if not commits:
        print("No commits yet.")
        return 0
    
    for commit in commits:
        timestamp = datetime.fromtimestamp(commit['timestamp'])
        print(f"commit {commit['hash']}")
        print(f"Author: {commit['author']}")
        print(f"Date:   {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n    {commit['message']}\n")
    
    return 0


def cmd_status(args):
    """Show repository status."""
    repo = Repository(args.path)
    if not repo.storage:
        print("Error: Not a CVCS repository. Run 'cvcs init' first.")
        return 1
    
    import json
    
    # Show current branch
    current_branch = repo.get_current_branch()
    print(f"On branch {current_branch}")
    
    # Show staged files
    index_file = repo.cvcs_dir / "index"
    if index_file.exists():
        index = json.loads(index_file.read_text())
        if index:
            print("\nChanges to be committed:")
            for file_path in index:
                print(f"  new file:   {file_path}")
        else:
            print("\nNothing staged for commit")
    
    return 0


def cmd_branch(args):
    """Branch operations."""
    repo = Repository(args.path)
    if not repo.storage:
        print("Error: Not a CVCS repository. Run 'cvcs init' first.")
        return 1
    
    branch_mgr = BranchManager(repo)
    
    if args.list:
        branches = branch_mgr.list_branches()
        current = repo.get_current_branch()
        
        if not branches:
            print("No branches yet. Create a commit first.")
            return 0
        
        for branch in branches:
            marker = "* " if branch == current else "  "
            print(f"{marker}{branch}")
        return 0
    
    if args.name:
        if branch_mgr.create_branch(args.name):
            print(f"Created branch '{args.name}'")
            return 0
        else:
            print(f"Error: Branch '{args.name}' already exists")
            return 1
    
    # Default: list branches
    branches = branch_mgr.list_branches()
    current = repo.get_current_branch()
    for branch in branches:
        marker = "* " if branch == current else "  "
        print(f"{marker}{branch}")
    return 0


def cmd_checkout(args):
    """Switch branches or restore files."""
    repo = Repository(args.path)
    if not repo.storage:
        print("Error: Not a CVCS repository. Run 'cvcs init' first.")
        return 1
    
    branch_mgr = BranchManager(repo)
    
    if args.branch:
        if branch_mgr.switch_branch(args.branch):
            print(f"Switched to branch '{args.branch}'")
            return 0
        else:
            print(f"Error: Branch '{args.branch}' does not exist")
            return 1
    
    if args.file:
        try:
            repo.checkout_file(args.file)
            print(f"Restored '{args.file}'")
            return 0
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    print("Error: Specify a branch with -b or file with -f")
    return 1


def cmd_merge(args):
    """Merge branches."""
    repo = Repository(args.path)
    if not repo.storage:
        print("Error: Not a CVCS repository. Run 'cvcs init' first.")
        return 1
    
    branch_mgr = BranchManager(repo)
    current_branch = repo.get_current_branch()
    
    result = branch_mgr.merge(args.source_branch)
    
    if "error" in result:
        print(f"Error: {result['error']}")
        return 1
    
    if result["success"]:
        print(f"Merged '{args.source_branch}' into '{current_branch}'")
        return 0
    else:
        print(f"Merge has conflicts:")
        for conflict in result["conflicts"]:
            file_path = conflict["file"]
            conflict_type = conflict["type"]
            print(f"  {file_path} ({conflict_type})")
        print("\nResolve conflicts and commit the result.")
        return 1


def main():
    """Main entry point for CVCS CLI."""
    parser = argparse.ArgumentParser(
        description="CVCS - Content Version Control System for all file types",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  cvcs init                      Initialize a new repository
  cvcs add file.docx data.csv   Add files to staging area
  cvcs commit -m "message"      Create a commit
  cvcs log                       View commit history
  cvcs branch feature-1         Create a new branch
  cvcs checkout -b feature-1    Switch to a branch
  cvcs merge feature-1          Merge a branch
        """
    )
    
    parser.add_argument('-C', '--path', default='.', 
                       help='Path to repository (default: current directory)')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # init command
    parser_init = subparsers.add_parser('init', help='Initialize a new repository')
    parser_init.set_defaults(func=cmd_init)
    
    # add command
    parser_add = subparsers.add_parser('add', help='Add files to staging area')
    parser_add.add_argument('files', nargs='+', help='Files to add')
    parser_add.set_defaults(func=cmd_add)
    
    # commit command
    parser_commit = subparsers.add_parser('commit', help='Create a commit')
    parser_commit.add_argument('-m', '--message', required=True, help='Commit message')
    parser_commit.add_argument('-a', '--author', default='CVCS User', help='Author name')
    parser_commit.set_defaults(func=cmd_commit)
    
    # log command
    parser_log = subparsers.add_parser('log', help='Show commit history')
    parser_log.add_argument('-n', '--max-count', type=int, default=10, 
                           help='Maximum number of commits to show')
    parser_log.add_argument('-b', '--branch', help='Branch to show log for')
    parser_log.set_defaults(func=cmd_log)
    
    # status command
    parser_status = subparsers.add_parser('status', help='Show repository status')
    parser_status.set_defaults(func=cmd_status)
    
    # branch command
    parser_branch = subparsers.add_parser('branch', help='Branch operations')
    parser_branch.add_argument('name', nargs='?', help='Branch name to create')
    parser_branch.add_argument('-l', '--list', action='store_true', 
                              help='List all branches')
    parser_branch.set_defaults(func=cmd_branch)
    
    # checkout command
    parser_checkout = subparsers.add_parser('checkout', 
                                           help='Switch branch or restore file')
    parser_checkout.add_argument('-b', '--branch', help='Branch to checkout')
    parser_checkout.add_argument('-f', '--file', help='File to restore')
    parser_checkout.set_defaults(func=cmd_checkout)
    
    # merge command
    parser_merge = subparsers.add_parser('merge', help='Merge branches')
    parser_merge.add_argument('source_branch', help='Branch to merge from')
    parser_merge.set_defaults(func=cmd_merge)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
