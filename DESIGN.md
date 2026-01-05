# Content Version Control System (CVCS) - Design Document

## Overview
CVCS is a content-based version control system that supports versioning and branching for all file types, including binary files like documents (.docx, .odt, .pdf) and data files (.csv, .json, .xml), unlike traditional Git which has limitations with binary files.

## Problem Statement
- **Git Limitation**: Binary files cannot be effectively branched and worked on in parallel
- **Git LFS Issue**: Locks files when being edited, preventing parallel work
- **Need**: A version control system that supports content-based versioning and branching for ALL file types

## Solution Architecture

### 1. Core Principles

#### Content-Addressable Storage
- Files are stored using SHA-256 hash of their content
- Identical content is stored only once (deduplication)
- Hash serves as unique identifier for any content version

#### Dual-Layer Storage
- **Raw Content**: Original binary data of files (for exact restoration)
- **Text Representation**: Extracted text content (for comparison and merging)
  - Documents (.docx, .odt, .pdf) → extracted text
  - Data files (.json, .xml, .csv) → normalized text
  - Text files (.txt, .rtf) → plain text

#### Parallel Branching for Binary Files
- No file locking mechanism
- Each branch maintains independent version history
- Content-based conflict detection during merge
- Smart merging using extracted text representations

### 2. Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     CVCS Architecture                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   CLI/API    │      │  Repository  │                     │
│  │   Interface  │─────▶│   Manager    │                     │
│  └──────────────┘      └──────────────┘                     │
│                              │                               │
│                    ┌─────────┴─────────┐                    │
│                    │                   │                    │
│         ┌──────────▼────────┐  ┌──────▼──────────┐         │
│         │   Content         │  │    Branch        │         │
│         │   Extractor       │  │    Manager       │         │
│         └──────────┬────────┘  └──────┬──────────┘         │
│                    │                   │                    │
│                    └─────────┬─────────┘                    │
│                              │                               │
│                    ┌─────────▼─────────┐                    │
│                    │  Content Storage   │                    │
│                    │  (Content-Address) │                    │
│                    └───────────────────┘                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3. Directory Structure

```
project-root/
├── .cvcs/                          # Repository metadata
│   ├── objects/                    # Content-addressable object store
│   │   ├── ab/                     # Hash prefix (first 2 chars)
│   │   │   └── cdef123...          # Hash suffix (remaining chars)
│   │   └── ...
│   ├── refs/                       # Branch references
│   │   ├── heads/                  # Branch heads
│   │   │   ├── main               # Main branch (commit hash)
│   │   │   ├── feature-1          # Feature branch
│   │   │   └── ...
│   │   └── tags/                   # Tags
│   ├── HEAD                        # Current branch reference
│   ├── index                       # Staging area (JSON)
│   └── config                      # Repository configuration
├── cvcs/                           # Python package
│   ├── __init__.py
│   ├── storage.py                  # Content storage module
│   ├── content_extractor.py       # File content extraction
│   ├── repository.py               # Repository operations
│   └── branch.py                   # Branching and merging
└── cvcs-cli.py                     # Command-line interface
```

### 4. Data Models

#### Commit Object
```json
{
  "type": "commit",
  "tree": {
    "path/to/file1.docx": {
      "content_hash": "sha256_of_raw_content",
      "text_hash": "sha256_of_extracted_text",
      "size": 12345
    },
    "path/to/file2.json": {
      "content_hash": "sha256_of_raw_content",
      "text_hash": "sha256_of_normalized_json",
      "size": 678
    }
  },
  "parent": "parent_commit_hash",
  "message": "Commit message",
  "author": "Author Name",
  "timestamp": 1234567890.123
}
```

#### Index (Staging Area)
```json
{
  "file1.txt": {
    "content_hash": "abc123...",
    "text_hash": "def456...",
    "size": 1024
  }
}
```

### 5. File Type Support

#### Supported File Types

| Category | Extensions | Extraction Method |
|----------|-----------|-------------------|
| **Text Files** | .txt, .rtf | Direct read with UTF-8 |
| **Documents** | .docx | python-docx library (paragraph text) |
| | .odt | odfpy library (paragraph text) |
| | .pdf | PyPDF2 library (page text) |
| **Data Files** | .json | Parse and normalize with sorted keys |
| | .xml | Parse and serialize to canonical form |
| | .csv | Read and normalize rows |
| **Code Files** | .py, .js, .java, etc. | Direct UTF-8 text |

#### Handling Unknown Binary Files
- Store raw content with SHA-256 hash
- No text extraction (text_hash = null)
- Merge conflicts require manual resolution

### 6. Key Operations

#### Initialize Repository
```bash
cvcs init
```
- Creates `.cvcs/` directory structure
- Initializes HEAD pointing to main branch
- Creates empty index and config

#### Add Files
```bash
cvcs add <file>
```
1. Extract content (raw + text if possible)
2. Store both in object database
3. Update index with file metadata and hashes

#### Commit
```bash
cvcs commit -m "message"
```
1. Read staged files from index
2. Create commit object with tree and metadata
3. Store commit object (gets hash)
4. Update current branch reference
5. Clear staging area

#### Branch Operations
```bash
cvcs branch <name>          # Create branch
cvcs checkout <branch>      # Switch branch
cvcs branches               # List branches
```

#### Merge with Conflict Detection
```bash
cvcs merge <source-branch>
```
1. Get trees from source and target branches
2. For each file:
   - If hashes match → no conflict
   - If text_hash available → 3-way merge with base
   - If binary only → mark as conflict, prefer source
3. Report conflicts to user
4. Create merge commit if successful

### 7. Parallel Work Support

#### Key Innovation: No File Locking
- **Traditional Git LFS**: Locks binary files, blocking parallel work
- **CVCS Approach**: 
  - Multiple developers can work on same file simultaneously
  - Each branch stores independent version
  - Intelligent merge using content comparison
  - Text extraction enables automatic merging for documents

#### Example Workflow
```
Developer A (branch: feature-a)
├── Edits document.docx
├── Commits changes
└── Text: "Section 1: Introduction\nSection 2: Analysis"

Developer B (branch: feature-b)
├── Edits same document.docx
├── Commits changes
└── Text: "Section 1: Overview\nSection 2: Analysis"

Merge:
├── Compare extracted text
├── Detect conflict in Section 1
├── Mark conflict with markers:
│   <<<<<<< SOURCE
│   Section 1: Introduction
│   =======
│   Section 1: Overview
│   >>>>>>> TARGET
└── User resolves manually
```

### 8. Advantages Over Git

| Feature | Git | Git LFS | CVCS |
|---------|-----|---------|------|
| Code versioning | ✅ | ✅ | ✅ |
| Binary file storage | ❌ (bloat) | ✅ | ✅ |
| Parallel binary editing | ❌ | ❌ (locks) | ✅ |
| Document text comparison | ❌ | ❌ | ✅ |
| Content deduplication | ✅ | ✅ | ✅ |
| Smart document merging | ❌ | ❌ | ✅ (text-based) |

### 9. Implementation Details

#### Content Storage (storage.py)
- SHA-256 hashing for content addressing
- Two-level directory structure (prefix/suffix)
- Stores both raw and metadata as objects
- Efficient retrieval by hash

#### Content Extraction (content_extractor.py)
- Plugin-based architecture for file types
- Graceful degradation (falls back to binary-only)
- Optional dependencies (docx, odfpy, PyPDF2)
- Normalized output for comparison

#### Repository Management (repository.py)
- Init, add, commit, checkout operations
- Index management (staging area)
- Branch reference management
- Commit history traversal

#### Branch Manager (branch.py)
- Create and switch branches
- Three-way merge algorithm
- Conflict detection and marking
- Text-based merge for documents

### 10. Future Enhancements

1. **Advanced Merging**
   - Semantic merge for structured documents
   - Image comparison for graphical files
   - Spreadsheet cell-level merging

2. **Performance Optimization**
   - Incremental text extraction
   - Caching mechanism
   - Compression for large files

3. **Collaboration Features**
   - Remote repository support
   - Push/pull operations
   - Conflict resolution UI

4. **Additional File Support**
   - .pptx (PowerPoint)
   - .xlsx (Excel) with cell-level tracking
   - Image diff visualization
   - Audio/video metadata tracking

### 11. Usage Example

```bash
# Initialize repository
$ cvcs init
Initialized empty CVCS repository in .cvcs/

# Add files
$ cvcs add report.docx data.csv presentation.pdf
Added 3 files to staging area

# Commit
$ cvcs commit -m "Initial version of project files"
[main abc123] Initial version of project files

# Create feature branch
$ cvcs branch feature-update
Created branch 'feature-update'

# Switch to feature branch
$ cvcs checkout feature-update
Switched to branch 'feature-update'

# Make changes, add, and commit
$ cvcs add report.docx
$ cvcs commit -m "Updated report with new findings"

# Switch back and merge
$ cvcs checkout main
$ cvcs merge feature-update
Merged feature-update into main
Conflicts in: report.docx (content differs)
  - Review .cvcs/conflicts/ for details

# View history
$ cvcs log
abc123 - Initial version of project files (2026-01-05)
def456 - Updated report with new findings (2026-01-05)
```

## Conclusion

CVCS provides a comprehensive solution for version control that works seamlessly with all file types, removing the limitations of traditional Git for binary files while maintaining the familiar branching and merging workflow. The content-based approach with intelligent text extraction enables parallel collaboration on documents and data files that was previously impossible with file-locking systems.
