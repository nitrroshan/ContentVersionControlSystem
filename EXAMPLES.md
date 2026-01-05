# CVCS Examples

This directory contains example usage scenarios for the Content Version Control System.

## Example 1: Basic Workflow

```bash
# Initialize a new CVCS repository
./cvcs-cli.py init

# Add files
echo "Hello, World!" > file.txt
./cvcs-cli.py add file.txt

# Commit
./cvcs-cli.py commit -m "Initial commit"

# View history
./cvcs-cli.py log
```

## Example 2: Branching and Merging

```bash
# Create a branch
./cvcs-cli.py branch feature-x

# Switch to the branch
./cvcs-cli.py checkout -b feature-x

# Make changes
echo "New content" >> file.txt
./cvcs-cli.py add file.txt
./cvcs-cli.py commit -m "Updated file"

# Switch back to main
./cvcs-cli.py checkout -b main

# Merge changes
./cvcs-cli.py merge feature-x
```

## Example 3: Working with Documents

```bash
# Add document files
./cvcs-cli.py add report.docx presentation.pdf data.csv

# Commit
./cvcs-cli.py commit -m "Added project documents"

# Create branch for each team member
./cvcs-cli.py branch alice-edits
./cvcs-cli.py branch bob-edits

# Alice works on her branch
./cvcs-cli.py checkout -b alice-edits
# Edit report.docx (Section 1)
./cvcs-cli.py add report.docx
./cvcs-cli.py commit -m "Updated introduction section"

# Bob works on his branch (simultaneously!)
./cvcs-cli.py checkout -b bob-edits
# Edit report.docx (Section 2)
./cvcs-cli.py add report.docx
./cvcs-cli.py commit -m "Added analysis section"

# Merge both (CVCS handles conflicts intelligently)
./cvcs-cli.py checkout -b main
./cvcs-cli.py merge alice-edits
./cvcs-cli.py merge bob-edits
```

## Example 4: Data Files with JSON

```bash
# Create a JSON configuration file
cat > config.json << 'EOF'
{
  "database": {
    "host": "localhost",
    "port": 5432
  },
  "features": {
    "auth": true,
    "logging": false
  }
}
EOF

# Track it
./cvcs-cli.py add config.json
./cvcs-cli.py commit -m "Initial configuration"

# Branch for development
./cvcs-cli.py branch dev-config
./cvcs-cli.py checkout -b dev-config

# Update config (CVCS normalizes JSON for comparison)
cat > config.json << 'EOF'
{
  "database": {
    "host": "dev.example.com",
    "port": 5432
  },
  "features": {
    "auth": true,
    "logging": true
  }
}
EOF

./cvcs-cli.py add config.json
./cvcs-cli.py commit -m "Dev environment config"

# Merge when ready
./cvcs-cli.py checkout -b main
./cvcs-cli.py merge dev-config
```

## Example 5: Viewing Status

```bash
# Check current status
./cvcs-cli.py status

# See which branch you're on
./cvcs-cli.py branch -l

# View commit history with limit
./cvcs-cli.py log -n 5
```

## Example 6: Restoring Files

```bash
# Accidentally modified a file
echo "Oops, wrong content" > important.txt

# Restore from last commit
./cvcs-cli.py checkout -f important.txt

# File is now restored to its committed state
```

## Running the Interactive Demo

A complete interactive demonstration is available:

```bash
./demo.sh
```

This will create a temporary repository and demonstrate:
- Initialization
- Adding multiple file types
- Committing changes
- Branching
- Merging
- Viewing history

## Notes

- CVCS works with **any file type**
- For best results with documents (.docx, .odt, .pdf), install optional dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Without optional libraries, binary files are still tracked but text extraction is not available
- All commands are safe and non-destructive - they only affect the `.cvcs` directory
