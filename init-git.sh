#!/bin/bash

# ===================================
# Prompt2Figma - Git Initialization Script
# ===================================
# This script initializes Git and GitHub for the project

set -e  # Exit on error

echo "🚀 Initializing Git for Prompt2Figma..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ===================================
# Step 1: Check Prerequisites
# ===================================
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed. Please install Git first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Git is installed${NC}"

if ! command -v gh &> /dev/null; then
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) is not installed. Some features will be limited.${NC}"
    echo -e "${YELLOW}   Install from: https://cli.github.com/${NC}"
    GH_AVAILABLE=false
else
    echo -e "${GREEN}✅ GitHub CLI is installed${NC}"
    GH_AVAILABLE=true
fi

echo ""

# ===================================
# Step 2: Configure Git
# ===================================
echo -e "${BLUE}Step 2: Configuring Git...${NC}"

# Check if user name is set
if [ -z "$(git config --global user.name)" ]; then
    read -p "Enter your name: " USER_NAME
    git config --global user.name "$USER_NAME"
fi
echo -e "${GREEN}✅ User name: $(git config --global user.name)${NC}"

# Check if user email is set
if [ -z "$(git config --global user.email)" ]; then
    read -p "Enter your email: " USER_EMAIL
    git config --global user.email "$USER_EMAIL"
fi
echo -e "${GREEN}✅ User email: $(git config --global user.email)${NC}"

# Set default branch name
git config --global init.defaultBranch main
echo -e "${GREEN}✅ Default branch set to 'main'${NC}"

# Enable color output
git config --global color.ui auto
echo -e "${GREEN}✅ Color output enabled${NC}"

echo ""

# ===================================
# Step 3: Initialize Repository
# ===================================
echo -e "${BLUE}Step 3: Initializing Git repository...${NC}"

if [ -d ".git" ]; then
    echo -e "${YELLOW}⚠️  Git repository already initialized${NC}"
else
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi

echo ""

# ===================================
# Step 4: Create Initial Commit
# ===================================
echo -e "${BLUE}Step 4: Creating initial commit...${NC}"

# Check if there are any commits
if git rev-parse HEAD >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Repository already has commits${NC}"
else
    git add .
    git commit -m "chore: initial project setup

- Add backend API with FastAPI
- Add Figma plugin frontend
- Add comprehensive documentation
- Add professional Git/GitHub setup
- Add CI/CD pipeline
- Add security policies"
    echo -e "${GREEN}✅ Initial commit created${NC}"
fi

echo ""

# ===================================
# Step 5: GitHub Setup
# ===================================
echo -e "${BLUE}Step 5: GitHub repository setup...${NC}"

if [ "$GH_AVAILABLE" = true ]; then
    read -p "Do you want to create a GitHub repository? (y/n): " CREATE_REPO
    
    if [ "$CREATE_REPO" = "y" ] || [ "$CREATE_REPO" = "Y" ]; then
        # Check if authenticated
        if ! gh auth status &> /dev/null; then
            echo -e "${YELLOW}⚠️  Not authenticated with GitHub. Running 'gh auth login'...${NC}"
            gh auth login
        fi
        
        read -p "Repository visibility (public/private): " VISIBILITY
        VISIBILITY=${VISIBILITY:-public}
        
        echo -e "${YELLOW}Creating GitHub repository...${NC}"
        gh repo create prompt2Figma --$VISIBILITY --source=. --remote=origin --push
        
        echo -e "${GREEN}✅ GitHub repository created and code pushed${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping GitHub repository creation${NC}"
        echo -e "${YELLOW}   You can create it manually later${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  GitHub CLI not available${NC}"
    echo -e "${YELLOW}   Create repository manually at: https://github.com/new${NC}"
    echo ""
    echo -e "${YELLOW}   Then run these commands:${NC}"
    echo -e "${YELLOW}   git remote add origin https://github.com/YOUR_USERNAME/prompt2Figma.git${NC}"
    echo -e "${YELLOW}   git branch -M main${NC}"
    echo -e "${YELLOW}   git push -u origin main${NC}"
fi

echo ""

# ===================================
# Step 6: Summary
# ===================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Git initialization complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Configure branch protection on GitHub"
echo "2. Add collaborators (if working in a team)"
echo "3. Add GitHub Actions secrets (GEMINI_API_KEY, etc.)"
echo "4. Review CONTRIBUTING.md for contribution guidelines"
echo "5. Start creating feature branches and PRs"
echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  git checkout -b feature/your-feature  # Create feature branch"
echo "  git add . && git commit -m 'feat: ...' # Commit changes"
echo "  git push origin feature/your-feature   # Push to GitHub"
echo "  gh pr create                           # Create pull request"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  - GIT_SETUP_GUIDE.md - Complete setup guide"
echo "  - CONTRIBUTING.md - Contribution guidelines"
echo "  - PROFESSIONAL_GIT_SETUP_SUMMARY.md - Quick reference"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
