# Content Version Control System (CVCS)

A version control system based on **content** for **all file types** - including documents, binary files, and code.

## Overview

Unlike traditional Git which has limitations with binary files (Git LFS requires file locking), CVCS enables:

✅ **Parallel branching and editing** of ALL file types, including binary files  
✅ **Content-based versioning** with intelligent text extraction for documents  
✅ **Smart merging** for documents (.docx, .odt, .pdf) using extracted text  
✅ **No file locking** - true parallel collaboration on binary files  

## Supported File Types

| Category | File Types | Features |
|----------|-----------|----------|
| **Documents** | `.docx`, `.odt`, `.pdf` | Text extraction, content comparison, smart merging |
| **Data Files** | `.json`, `.xml`, `.csv` | Normalized comparison, semantic merging |
| **Text Files** | `.txt`, `.rtf`, code files | Line-by-line diff and merge |
| **Binary Files** | Any other format | Version tracking, hash-based comparison |

## Installation

```bash
# Clone the repository
git clone https://github.com/nitrroshan/ContentVersionControlSystem.git
cd ContentVersionControlSystem

# Install optional dependencies for enhanced document support
pip install -r requirements.txt

# Make CLI executable
chmod +x cvcs-cli.py
```

## Quick Start

```bash
# Initialize a new repository
./cvcs-cli.py init

# Add files (any type!)
./cvcs-cli.py add document.docx report.pdf data.csv code.py

# Create a commit
./cvcs-cli.py commit -m "Initial version"

# Create a branch for parallel work
./cvcs-cli.py branch feature-updates

# Switch to the branch
./cvcs-cli.py checkout -b feature-updates

# Make changes, add, and commit
./cvcs-cli.py add document.docx
./cvcs-cli.py commit -m "Updated document"

# Switch back to main and merge
./cvcs-cli.py checkout -b main
./cvcs-cli.py merge feature-updates

# View history
./cvcs-cli.py log
```

## Key Features

### 1. Content-Addressable Storage
Files are stored using SHA-256 hashing of their content, ensuring:
- **Deduplication**: Identical content stored only once
- **Integrity**: Content verification through hashing
- **Efficiency**: Fast content lookup

### 2. Dual-Layer Storage
Each file is stored in two representations:
- **Raw bytes**: For exact file restoration
- **Extracted text**: For intelligent comparison and merging

### 3. Parallel Work on Binary Files
```bash
# Developer A on branch feature-a
./cvcs-cli.py checkout -b feature-a
# Edit document.docx with changes to Section 1
./cvcs-cli.py add document.docx
./cvcs-cli.py commit -m "Updated Section 1"

# Developer B on branch feature-b (simultaneously!)
./cvcs-cli.py checkout -b feature-b
# Edit same document.docx with changes to Section 2
./cvcs-cli.py add document.docx
./cvcs-cli.py commit -m "Updated Section 2"

# Merge - CVCS detects and handles conflicts intelligently
./cvcs-cli.py checkout -b main
./cvcs-cli.py merge feature-a
./cvcs-cli.py merge feature-b
```

### 4. Smart Document Merging
When merging documents, CVCS:
1. Extracts text content from both versions
2. Performs three-way merge (base, source, target)
3. Detects conflicts in modified sections
4. Marks conflicts with clear markers for manual resolution

## Commands

### Repository Management
```bash
./cvcs-cli.py init                     # Initialize repository
./cvcs-cli.py status                   # Show repository status
```

### Working with Files
```bash
./cvcs-cli.py add <file>...           # Add files to staging
./cvcs-cli.py commit -m "message"     # Create commit
./cvcs-cli.py log                      # View commit history
./cvcs-cli.py log -n 5                # Show last 5 commits
```

### Branching
```bash
./cvcs-cli.py branch                   # List branches
./cvcs-cli.py branch <name>           # Create branch
./cvcs-cli.py checkout -b <name>      # Switch branch
./cvcs-cli.py merge <branch>          # Merge branch
```

### File Operations
```bash
./cvcs-cli.py checkout -f <file>      # Restore file from HEAD
```

## Architecture

See [DESIGN.md](DESIGN.md) for complete design documentation and [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture diagrams.

### Key Components

- **Storage Layer** (`cvcs/storage.py`): Content-addressable object store using SHA-256
- **Content Extractor** (`cvcs/content_extractor.py`): Extracts text from various file formats
- **Repository Manager** (`cvcs/repository.py`): Handles commits, staging, and history
- **Branch Manager** (`cvcs/branch.py`): Manages branches and merging with conflict detection

## Advantages Over Git

| Feature | Git | Git LFS | CVCS |
|---------|-----|---------|------|
| Code versioning | ✅ | ✅ | ✅ |
| Binary file storage | ❌ (bloats repo) | ✅ | ✅ |
| Parallel binary editing | ❌ | ❌ (locks files) | ✅ |
| Document content comparison | ❌ | ❌ | ✅ |
| Smart document merging | ❌ | ❌ | ✅ |
| No file locking | ✅ | ❌ | ✅ |

## Examples

### Example 1: Collaborative Document Editing

```bash
# Project lead initializes repository
./cvcs-cli.py init
./cvcs-cli.py add project-proposal.docx budget.xlsx timeline.pdf
./cvcs-cli.py commit -m "Initial project documents"

# Team member A works on proposal
./cvcs-cli.py branch proposal-updates
./cvcs-cli.py checkout -b proposal-updates
# Edit project-proposal.docx
./cvcs-cli.py add project-proposal.docx
./cvcs-cli.py commit -m "Added technical approach section"

# Team member B works on proposal simultaneously
./cvcs-cli.py branch budget-updates
./cvcs-cli.py checkout -b budget-updates
# Edit project-proposal.docx (different sections)
./cvcs-cli.py add project-proposal.docx
./cvcs-cli.py commit -m "Updated budget section"

# Merge both changes
./cvcs-cli.py checkout -b main
./cvcs-cli.py merge proposal-updates
./cvcs-cli.py merge budget-updates
# CVCS automatically merges non-conflicting sections!
```

### Example 2: Data File Versioning

```bash
# Track data files with semantic comparison
./cvcs-cli.py add data.json config.xml results.csv

# JSON files are normalized for comparison
# Changes to formatting don't create false conflicts
./cvcs-cli.py commit -m "Updated configuration"

# Branch for data analysis
./cvcs-cli.py branch analysis
./cvcs-cli.py checkout -b analysis
# Modify data.json
./cvcs-cli.py add data.json
./cvcs-cli.py commit -m "Added analysis results"

./cvcs-cli.py log  # View complete history
```

## Technical Details

### Repository Structure
```
project/
├── .cvcs/                    # Repository metadata
│   ├── objects/              # Content-addressable storage
│   │   ├── ab/
│   │   │   └── cdef123...   # Stored objects
│   ├── refs/
│   │   └── heads/           # Branch references
│   │       ├── main
│   │       └── feature-1
│   ├── HEAD                 # Current branch pointer
│   ├── index                # Staging area
│   └── config               # Repository config
└── your-files...
```

### Dependencies

**Optional** (for enhanced functionality):
- `python-docx`: Extract text from .docx files
- `odfpy`: Extract text from .odt files
- `PyPDF2`: Extract text from .pdf files

CVCS works without these but with reduced functionality for those file types.

## Contributing

Contributions are welcome! Areas for enhancement:
- Additional file format support (.xlsx, .pptx)
- Advanced merge algorithms
- Remote repository support (push/pull)
- Web-based conflict resolution UI
- Performance optimizations

## License

See [LICENSE](LICENSE) file for details.

## Learn More

- [Design Documentation](DESIGN.md) - Comprehensive design and requirements
- [Architecture Guide](ARCHITECTURE.md) - Technical architecture and data flows

---

**CVCS - Version control that works for ALL your files, not just code!** 🚀
