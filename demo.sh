#!/bin/bash
# CVCS Demo Script
# Demonstrates the key features of Content Version Control System

set -e

echo "=== CVCS Demo: Content-Based Version Control for All Files ==="
echo ""

# Create demo directory
DEMO_DIR="/tmp/cvcs_demo_$(date +%s)"
mkdir -p "$DEMO_DIR"
cd "$DEMO_DIR"

CVCS_CLI="/home/runner/work/ContentVersionControlSystem/ContentVersionControlSystem/cvcs-cli.py"

echo "Step 1: Initialize repository"
$CVCS_CLI init
echo ""

echo "Step 2: Create sample files"
cat > report.txt << 'EOF'
Project Report
==============

Introduction
------------
This is the initial version of our project report.

Analysis
--------
Initial analysis shows promising results.

Conclusion
----------
More work needed.
EOF

cat > data.json << 'EOF'
{
  "project": "CVCS",
  "status": "development",
  "features": ["branching", "merging", "all file types"]
}
EOF

cat > config.xml << 'EOF'
<?xml version="1.0"?>
<config>
  <setting name="version">1.0</setting>
  <setting name="mode">demo</setting>
</config>
EOF

echo "Created: report.txt, data.json, config.xml"
echo ""

echo "Step 3: Add and commit files"
$CVCS_CLI add report.txt data.json config.xml
$CVCS_CLI commit -m "Initial project files"
echo ""

echo "Step 4: Create a feature branch for parallel work"
$CVCS_CLI branch feature-updates
echo ""

echo "Step 5: Switch to feature branch"
$CVCS_CLI checkout -b feature-updates
echo ""

echo "Step 6: Make changes in feature branch"
cat > report.txt << 'EOF'
Project Report
==============

Introduction
------------
This is the UPDATED version of our project report.

Analysis
--------
Detailed analysis shows excellent results with CVCS!

Conclusion
----------
CVCS enables parallel work on all file types!
EOF

$CVCS_CLI add report.txt
$CVCS_CLI commit -m "Updated report with findings"
echo ""

echo "Step 7: Switch back to main branch"
$CVCS_CLI checkout -b main
echo ""

echo "Step 8: View commit history"
$CVCS_CLI log
echo ""

echo "Step 9: List all branches"
$CVCS_CLI branch -l
echo ""

echo "Step 10: Merge feature branch into main"
$CVCS_CLI merge feature-updates
echo ""

echo "Step 11: View final commit log"
$CVCS_CLI log -n 5
echo ""

echo "=== Demo Complete! ==="
echo ""
echo "Key Achievements:"
echo "✓ Version control for all file types (text, JSON, XML)"
echo "✓ Parallel branching without file locking"
echo "✓ Content-based storage with deduplication"
echo "✓ Smart merging with conflict detection"
echo ""
echo "Demo repository located at: $DEMO_DIR"
echo "Explore with: cd $DEMO_DIR && $CVCS_CLI status"
