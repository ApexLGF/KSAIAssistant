#!/bin/bash

# Initialize Git repository for TestAIAgent

echo "Initializing Git repository..."

# Initialize git if not already done
if [ ! -d .git ]; then
    git init
    echo "Git repository initialized"
else
    echo "Git repository already exists"
fi

# Add all files
git add .

# Show status
echo ""
echo "Files to be committed:"
git status --short

echo ""
echo "Ready to commit. Run:"
echo "  git commit -m 'Initial commit: Everlasting Cabinetry Sales Assistant'"
echo "  git remote add origin <your-repo-url>"
echo "  git push -u origin main"
