# Git & GitHub Setup Guide - Prompt2Figma

This guide will help you set up Git and GitHub for the Prompt2Figma project following professional, enterprise-level standards.

---

## Table of Contents

1. [Initial Git Setup](#initial-git-setup)
2. [GitHub Repository Setup](#github-repository-setup)
3. [Branch Strategy](#branch-strategy)
4. [Commit Conventions](#commit-conventions)
5. [GitHub Actions Setup](#github-actions-setup)
6. [Team Collaboration](#team-collaboration)
7. [Best Practices](#best-practices)

---

## Initial Git Setup

### 1. Install Git

**Windows:**
```bash
# Download from https://git-scm.com/download/win
# Or use winget
winget install Git.Git
```

**macOS:**
```bash
brew install git
```

**Linux:**
```bash
sudo apt-get install git  # Debian/Ubuntu
sudo yum install git      # CentOS/RHEL
```

### 2. Configure Git

```bash
# Set your identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default branch name
git config --global init.defaultBranch main

# Set default editor
git config --global core.editor "code --wait"  # VS Code
# OR
git config --global core.editor "vim"          # Vim

# Enable color output
git config --global color.ui auto

# Set line ending handling
git config --global core.autocrlf input  # macOS/Linux
git config --global core.autocrlf true   # Windows

# Enable credential caching
git config --global credential.helper cache  # Linux/macOS
git config --global credential.helper wincred  # Windows
```

### 3. Initialize Repository

```bash
# Navigate to project directory
cd prompt2Figma

# Initialize Git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "chore: initial project setup"
```

---

## GitHub Repository Setup

### 1. Create GitHub Repository

**Option A: Via GitHub Website**
1. Go to https://github.com/new
2. Repository name: `prompt2Figma`
3. Description: "AI-powered Figma plugin for generating wireframes and React code"
4. Visibility: Public or Private
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

**Option B: Via GitHub CLI**
```bash
# Install GitHub CLI
# Windows: winget install GitHub.cli
# macOS: brew install gh
# Linux: See https://github.com/cli/cli#installation

# Authenticate
gh auth login

# Create repository
gh repo create prompt2Figma --public --source=. --remote=origin --push
```

### 2. Connect Local Repository to GitHub

```bash
# Add remote origin
git remote add origin https://github.com/YOUR_USERNAME/prompt2Figma.git

# Verify remote
git remote -v

# Push to GitHub
git branch -M main
git push -u origin main
```

### 3. Configure Repository Settings

**On GitHub Website:**

1. **General Settings**
   - Enable "Automatically delete head branches"
   - Disable "Allow merge commits" (use squash or rebase)
   - Enable "Allow squash merging"
   - Enable "Allow rebase merging"

2. **Branch Protection Rules** (Settings → Branches)
   - Branch name pattern: `main`
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Require conversation resolution before merging
   - ✅ Include administrators
   - ✅ Restrict who can push to matching branches

3. **Enable GitHub Features**
   - ✅ Issues
   - ✅ Projects
   - ✅ Wiki (optional)
   - ✅ Discussions (optional)
   - ✅ Sponsorships (optional)

4. **Add Topics/Tags**
   - `figma-plugin`
   - `ai`
   - `wireframe`
   - `react`
   - `typescript`
   - `python`
   - `fastapi`

---

## Branch Strategy

We follow **Git Flow** with modifications for modern development.

### Branch Types

```
main (production)
  ↓
develop (integration)
  ↓
feature/* (new features)
bugfix/* (bug fixes)
hotfix/* (urgent production fixes)
release/* (release preparation)
```

### Branch Naming Convention

```bash
# Features
feature/add-dark-mode
feature/implement-export-png

# Bug Fixes
bugfix/fix-device-selector
bugfix/resolve-memory-leak

# Hotfixes
hotfix/critical-security-patch
hotfix/fix-crash-on-startup

# Releases
release/v1.2.0
release/v2.0.0-beta.1
```

### Creating Branches

```bash
# Create and switch to new feature branch
git checkout -b feature/your-feature-name

# Create from specific branch
git checkout -b feature/your-feature develop

# Push branch to GitHub
git push -u origin feature/your-feature-name
```

### Branch Workflow

```bash
# 1. Update your local main/develop
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/new-feature

# 3. Make changes and commit
git add .
git commit -m "feat: add new feature"

# 4. Keep branch updated
git fetch origin
git rebase origin/main

# 5. Push to GitHub
git push origin feature/new-feature

# 6. Create Pull Request on GitHub

# 7. After PR is merged, delete branch
git checkout main
git pull origin main
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

---

## Commit Conventions

We follow **Conventional Commits** specification.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `style` - Code style (formatting, semicolons, etc.)
- `refactor` - Code refactoring
- `perf` - Performance improvement
- `test` - Adding/updating tests
- `chore` - Maintenance tasks
- `ci` - CI/CD changes
- `build` - Build system changes
- `revert` - Revert previous commit

### Examples

```bash
# Simple commit
git commit -m "feat(plugin): add dark mode support"

# Commit with body
git commit -m "fix(backend): resolve session timeout issue

Fix race condition in session cleanup that caused premature
session expiration. Add additional logging for debugging.

Fixes #456"

# Breaking change
git commit -m "feat(api)!: change authentication method

BREAKING CHANGE: API now requires OAuth2 instead of API keys.
Users must update their authentication configuration."
```

### Commit Best Practices

```bash
# Stage specific files
git add file1.js file2.py

# Stage all changes
git add .

# Stage interactively
git add -p

# Amend last commit (before pushing)
git commit --amend

# View commit history
git log --oneline --graph --all

# View changes
git diff
git diff --staged
```

---

## GitHub Actions Setup

### 1. Add Secrets

Go to: Settings → Secrets and variables → Actions

Add these secrets:
- `GEMINI_API_KEY` - Your Google Gemini API key
- `CODECOV_TOKEN` - Codecov token (optional)

### 2. Enable Actions

1. Go to Actions tab
2. Enable workflows
3. Workflows will run automatically on push/PR

### 3. Status Badges

Add to README.md:

```markdown
![CI/CD](https://github.com/YOUR_USERNAME/prompt2Figma/workflows/CI%2FCD%20Pipeline/badge.svg)
![Coverage](https://codecov.io/gh/YOUR_USERNAME/prompt2Figma/branch/main/graph/badge.svg)
![License](https://img.shields.io/github/license/YOUR_USERNAME/prompt2Figma)
![Version](https://img.shields.io/github/v/release/YOUR_USERNAME/prompt2Figma)
```

---

## Team Collaboration

### 1. Add Collaborators

Settings → Collaborators → Add people

**Roles:**
- **Admin** - Full access
- **Maintain** - Manage without admin access
- **Write** - Push to repository
- **Triage** - Manage issues and PRs
- **Read** - View and clone

### 2. Create Teams (for Organizations)

Settings → Teams → New team

**Example Teams:**
- `@prompt2figma/core` - Core maintainers
- `@prompt2figma/frontend` - Frontend developers
- `@prompt2figma/backend` - Backend developers
- `@prompt2figma/reviewers` - Code reviewers

### 3. Code Review Process

```bash
# 1. Create PR
gh pr create --title "feat: add feature" --body "Description"

# 2. Request reviewers
gh pr edit --add-reviewer @username

# 3. Address feedback
git add .
git commit -m "fix: address review comments"
git push

# 4. Merge after approval
gh pr merge --squash
```

### 4. Issue Management

```bash
# Create issue
gh issue create --title "Bug: something broken" --body "Description"

# List issues
gh issue list

# Assign issue
gh issue edit 123 --add-assignee @username

# Close issue
gh issue close 123
```

---

## Best Practices

### 1. Commit Frequency

✅ **DO:**
- Commit often (logical units of work)
- Commit working code
- Write descriptive messages

❌ **DON'T:**
- Commit broken code
- Make huge commits
- Use vague messages like "fix stuff"

### 2. Pull Requests

✅ **DO:**
- Keep PRs small and focused
- Write clear descriptions
- Link related issues
- Request specific reviewers
- Respond to feedback promptly

❌ **DON'T:**
- Create massive PRs
- Mix unrelated changes
- Ignore review comments
- Force push after review started

### 3. Branch Management

✅ **DO:**
- Delete merged branches
- Keep branches up to date
- Use descriptive names
- Create from correct base branch

❌ **DON'T:**
- Keep stale branches
- Work on main directly
- Use generic names like "fix"
- Create long-lived feature branches

### 4. Code Review

✅ **DO:**
- Review code thoroughly
- Test changes locally
- Provide constructive feedback
- Approve when satisfied

❌ **DON'T:**
- Rubber-stamp approvals
- Be overly critical
- Ignore security issues
- Approve without testing

### 5. Git Hygiene

```bash
# Clean up local branches
git branch --merged | grep -v "\*" | xargs -n 1 git branch -d

# Update all branches
git fetch --all --prune

# View branch status
git branch -vv

# Stash changes temporarily
git stash
git stash pop

# Cherry-pick specific commit
git cherry-pick <commit-hash>

# Revert commit
git revert <commit-hash>
```

---

## Useful Git Commands

### Daily Workflow

```bash
# Start work
git checkout main
git pull origin main
git checkout -b feature/my-feature

# During work
git status
git diff
git add .
git commit -m "feat: add feature"

# Before pushing
git fetch origin
git rebase origin/main
git push origin feature/my-feature

# After PR merged
git checkout main
git pull origin main
git branch -d feature/my-feature
```

### Troubleshooting

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Discard local changes
git checkout -- file.txt
git restore file.txt

# Update commit message
git commit --amend -m "new message"

# Resolve merge conflicts
git status  # See conflicted files
# Edit files to resolve conflicts
git add .
git commit

# Abort merge
git merge --abort

# Abort rebase
git rebase --abort
```

### Advanced

```bash
# Interactive rebase (clean up commits)
git rebase -i HEAD~3

# Find bug with bisect
git bisect start
git bisect bad
git bisect good <commit>

# View file history
git log --follow file.txt

# Search commits
git log --grep="search term"

# View who changed what
git blame file.txt

# Create tag
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

---

## GitHub CLI Cheat Sheet

```bash
# Authentication
gh auth login
gh auth status

# Repository
gh repo create
gh repo clone
gh repo view

# Pull Requests
gh pr create
gh pr list
gh pr view 123
gh pr checkout 123
gh pr merge 123
gh pr review 123

# Issues
gh issue create
gh issue list
gh issue view 123
gh issue close 123

# Releases
gh release create v1.0.0
gh release list
gh release view v1.0.0
```

---

## Resources

### Documentation
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Docs](https://docs.github.com)
- [Conventional Commits](https://www.conventionalcommits.org)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)

### Tools
- [GitHub Desktop](https://desktop.github.com/)
- [GitKraken](https://www.gitkraken.com/)
- [Sourcetree](https://www.sourcetreeapp.com/)
- [GitHub CLI](https://cli.github.com/)

### Learning
- [Learn Git Branching](https://learngitbranching.js.org/)
- [Git Immersion](https://gitimmersion.com/)
- [Pro Git Book](https://git-scm.com/book/en/v2)

---

## Quick Start Checklist

- [ ] Install Git
- [ ] Configure Git identity
- [ ] Initialize repository
- [ ] Create GitHub repository
- [ ] Connect local to remote
- [ ] Configure branch protection
- [ ] Add collaborators
- [ ] Set up GitHub Actions
- [ ] Add secrets
- [ ] Create first PR
- [ ] Review and merge

---

## Support

For questions or issues with Git/GitHub setup:
- Open an issue on GitHub
- Check [GitHub Community](https://github.community/)
- Read [Git documentation](https://git-scm.com/doc)

---

**Happy coding! 🚀**
