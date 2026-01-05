# Architecture Overview

## System Components

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  cvcs init   │  │  cvcs add    │  │ cvcs commit  │   ...     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼──────────────────┐
│         ▼                  ▼                  ▼                   │
│  ┌────────────────────────────────────────────────────┐          │
│  │           Repository Manager (repository.py)       │          │
│  │                                                     │          │
│  │  - Initialize repository (.cvcs directory)         │          │
│  │  - Manage staging area (index)                     │          │
│  │  - Create and retrieve commits                     │          │
│  │  - Track branch references                         │          │
│  │  - Checkout files from commits                     │          │
│  └──────────┬─────────────────────────┬────────────────┘         │
│             │                         │                           │
│             ▼                         ▼                           │
│  ┌───────────────────────┐  ┌──────────────────────┐            │
│  │  Content Extractor    │  │   Branch Manager     │            │
│  │ (content_extractor.py)│  │    (branch.py)       │            │
│  │                       │  │                      │            │
│  │ - Extract text from   │  │ - Create branches    │            │
│  │   .docx, .odt, .pdf   │  │ - Switch branches    │            │
│  │ - Normalize .json,    │  │ - Merge branches     │            │
│  │   .xml, .csv          │  │ - Detect conflicts   │            │
│  │ - Handle text files   │  │ - 3-way merge        │            │
│  └───────────┬───────────┘  └──────────┬───────────┘            │
│              │                          │                         │
└──────────────┼──────────────────────────┼─────────────────────────┘
               │                          │
┌──────────────┼──────────────────────────┼─────────────────────────┐
│              ▼                          ▼                          │
│  ┌────────────────────────────────────────────────────┐           │
│  │       Content Storage (storage.py)                 │           │
│  │                                                     │           │
│  │  ┌──────────────────────────────────────────────┐  │           │
│  │  │  Content-Addressable Object Store            │  │           │
│  │  │                                               │  │           │
│  │  │  Objects stored by SHA-256 hash:             │  │           │
│  │  │  .cvcs/objects/ab/cdef123...                 │  │           │
│  │  │                                               │  │           │
│  │  │  Each file has TWO representations:          │  │           │
│  │  │  1. Raw binary content (exact bytes)         │  │           │
│  │  │  2. Text representation (for comparison)     │  │           │
│  │  └──────────────────────────────────────────────┘  │           │
│  │                                                     │           │
│  │  ┌──────────────────────────────────────────────┐  │           │
│  │  │  Metadata Storage                            │  │           │
│  │  │                                               │  │           │
│  │  │  - Commits (tree + parent + message)         │  │           │
│  │  │  - Branch references (commit hashes)         │  │           │
│  │  │  - Index/staging area (file → hashes)        │  │           │
│  │  └──────────────────────────────────────────────┘  │           │
│  └────────────────────────────────────────────────────┘           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Adding and Committing Files
```
┌──────────────┐
│  User File   │
│  (any type)  │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│  Content Extractor                   │
│  ┌────────────────────────────────┐  │
│  │ Read raw bytes                 │  │
│  │ Extract text (if supported)    │  │
│  └────────────────────────────────┘  │
└──────┬───────────────────┬───────────┘
       │                   │
       │ Raw Content       │ Text Content
       │                   │
       ▼                   ▼
┌─────────────────────────────────────┐
│  Content Storage                    │
│  ┌───────────┐      ┌────────────┐  │
│  │ Store raw │      │Store text  │  │
│  │ → hash1   │      │ → hash2    │  │
│  └───────────┘      └────────────┘  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Index (Staging)                    │
│  {                                  │
│    "file.docx": {                   │
│      "content_hash": "hash1",       │
│      "text_hash": "hash2",          │
│      "size": 12345                  │
│    }                                │
│  }                                  │
└──────┬──────────────────────────────┘
       │ cvcs commit
       ▼
┌─────────────────────────────────────┐
│  Commit Object                      │
│  {                                  │
│    "tree": { ... index ... },       │
│    "parent": "prev_commit_hash",    │
│    "message": "...",                │
│    "author": "...",                 │
│    "timestamp": 123456              │
│  }                                  │
│  → stored as hash3                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Branch Reference                   │
│  .cvcs/refs/heads/main → hash3      │
└─────────────────────────────────────┘
```

### Branching and Merging
```
Main Branch:
   commit1 → commit2 → commit3
                        (file.docx v1)
                        
Feature Branch (from commit2):
   commit2 → commit4
             (file.docx v2)

Merge Process:
┌─────────────────────────────────────────────┐
│  1. Get commit trees                        │
│     Main:    file.docx → hash_main          │
│     Feature: file.docx → hash_feature       │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  2. Compare content hashes                  │
│     hash_main ≠ hash_feature → CONFLICT     │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  3. Check for text representations          │
│     Both have text_hash? → Try text merge   │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  4. Three-way merge                         │
│     Base:    text from commit2              │
│     Source:  text from feature              │
│     Target:  text from main                 │
│                                             │
│     If both changed differently:            │
│     <<<<<<< SOURCE                          │
│     Feature text                            │
│     =======                                 │
│     Main text                               │
│     >>>>>>> TARGET                          │
└──────┬──────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  5. Report conflicts or auto-merge          │
│     User resolves conflicts manually        │
│     Then creates merge commit               │
└─────────────────────────────────────────────┘
```

## File Type Handling Strategy

### Document Files (.docx, .odt, .pdf)
```
Original File (.docx)
    ├─→ Raw Storage (ZIP archive with XML)
    │   Purpose: Exact restoration of file
    │
    └─→ Text Extraction (paragraphs concatenated)
        Purpose: Content comparison and merging
        
Example:
  Raw: [Binary ZIP data]
  Text: "Introduction\nThis document describes...\nConclusion\n"
```

### Data Files (.json, .xml, .csv)
```
Original File (.json)
    ├─→ Raw Storage (exact bytes)
    │   Purpose: Preserve formatting, comments
    │
    └─→ Normalized Text (sorted, formatted)
        Purpose: Semantic comparison
        
Example:
  Raw: {"name":"John","age":30}
  Normalized: {
    "age": 30,
    "name": "John"
  }
```

### Binary Files (unknown types)
```
Original File (.bin)
    └─→ Raw Storage only
        Purpose: Version tracking
        Note: No text merge, hash comparison only
```

## Key Design Decisions

### 1. Why SHA-256 instead of SHA-1?
- Better security (Git is moving to SHA-256)
- Collision resistance
- Future-proof

### 2. Why store both raw and text?
- Raw: Exact file restoration
- Text: Enable intelligent merging
- Trade-off: More storage, better functionality

### 3. Why no file locking?
- Git LFS locks prevent parallel work
- Content-based approach allows true parallelism
- Conflicts detected at merge time, not edit time

### 4. Why extract text from documents?
- Enables semantic comparison
- Allows automatic merging when possible
- Shows meaningful diffs to users

### 5. How is this different from Git?
```
Git:
  ✓ Excellent for text/code
  ✗ Poor for binary files (repo bloat)
  ✗ Git LFS locks files

CVCS:
  ✓ Designed for ALL file types
  ✓ No file locking
  ✓ Smart document merging
  ✓ Content deduplication
```

## Implementation Technologies

### Core: Python
- **Why?** Cross-platform, rich ecosystem, easy to extend
- **Standard Library**: hashlib, json, pathlib, difflib
- **Optional Dependencies**:
  - python-docx: .docx files
  - odfpy: .odt files
  - PyPDF2: .pdf files

### Storage: File System
- **Why?** Simple, portable, no database overhead
- **Structure**: Content-addressable (like Git)
- **Performance**: O(1) lookup by hash

### Merge Algorithm: Three-Way Merge
- **Why?** Industry standard, well understood
- **Base**: Common ancestor
- **Source**: Changes from feature branch
- **Target**: Changes in current branch
