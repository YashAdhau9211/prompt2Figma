@echo off
REM ===================================
REM Prompt2Figma - Git Initialization Script (Windows)
REM ===================================

echo.
echo ========================================
echo Prompt2Figma - Git Initialization
echo ========================================
echo.

REM ===================================
REM Step 1: Check Prerequisites
REM ===================================
echo Step 1: Checking prerequisites...
echo.

where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed. Please install Git first.
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo [OK] Git is installed

where gh >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] GitHub CLI is not installed. Some features will be limited.
    echo Install from: https://cli.github.com/
    set GH_AVAILABLE=false
) else (
    echo [OK] GitHub CLI is installed
    set GH_AVAILABLE=true
)

echo.

REM ===================================
REM Step 2: Configure Git
REM ===================================
echo Step 2: Configuring Git...
echo.

REM Check if user name is set
git config --global user.name >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    set /p USER_NAME="Enter your name: "
    git config --global user.name "%USER_NAME%"
)
for /f "delims=" %%i in ('git config --global user.name') do set GIT_USER=%%i
echo [OK] User name: %GIT_USER%

REM Check if user email is set
git config --global user.email >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    set /p USER_EMAIL="Enter your email: "
    git config --global user.email "%USER_EMAIL%"
)
for /f "delims=" %%i in ('git config --global user.email') do set GIT_EMAIL=%%i
echo [OK] User email: %GIT_EMAIL%

REM Set default branch name
git config --global init.defaultBranch main
echo [OK] Default branch set to 'main'

REM Enable color output
git config --global color.ui auto
echo [OK] Color output enabled

REM Set line ending handling for Windows
git config --global core.autocrlf true
echo [OK] Line ending handling configured

echo.

REM ===================================
REM Step 3: Initialize Repository
REM ===================================
echo Step 3: Initializing Git repository...
echo.

if exist ".git" (
    echo [WARNING] Git repository already initialized
) else (
    git init
    echo [OK] Git repository initialized
)

echo.

REM ===================================
REM Step 4: Create Initial Commit
REM ===================================
echo Step 4: Creating initial commit...
echo.

git rev-parse HEAD >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [WARNING] Repository already has commits
) else (
    git add .
    git commit -m "chore: initial project setup" -m "- Add backend API with FastAPI" -m "- Add Figma plugin frontend" -m "- Add comprehensive documentation" -m "- Add professional Git/GitHub setup" -m "- Add CI/CD pipeline" -m "- Add security policies"
    echo [OK] Initial commit created
)

echo.

REM ===================================
REM Step 5: GitHub Setup
REM ===================================
echo Step 5: GitHub repository setup...
echo.

if "%GH_AVAILABLE%"=="true" (
    set /p CREATE_REPO="Do you want to create a GitHub repository? (y/n): "
    
    if /i "%CREATE_REPO%"=="y" (
        REM Check if authenticated
        gh auth status >nul 2>nul
        if %ERRORLEVEL% NEQ 0 (
            echo [WARNING] Not authenticated with GitHub. Running 'gh auth login'...
            gh auth login
        )
        
        set /p VISIBILITY="Repository visibility (public/private) [public]: "
        if "%VISIBILITY%"=="" set VISIBILITY=public
        
        echo Creating GitHub repository...
        gh repo create prompt2Figma --%VISIBILITY% --source=. --remote=origin --push
        
        echo [OK] GitHub repository created and code pushed
    ) else (
        echo [WARNING] Skipping GitHub repository creation
        echo You can create it manually later
    )
) else (
    echo [WARNING] GitHub CLI not available
    echo Create repository manually at: https://github.com/new
    echo.
    echo Then run these commands:
    echo   git remote add origin https://github.com/YOUR_USERNAME/prompt2Figma.git
    echo   git branch -M main
    echo   git push -u origin main
)

echo.

REM ===================================
REM Step 6: Summary
REM ===================================
echo ========================================
echo [SUCCESS] Git initialization complete!
echo ========================================
echo.
echo Next steps:
echo 1. Configure branch protection on GitHub
echo 2. Add collaborators (if working in a team)
echo 3. Add GitHub Actions secrets (GEMINI_API_KEY, etc.)
echo 4. Review CONTRIBUTING.md for contribution guidelines
echo 5. Start creating feature branches and PRs
echo.
echo Useful commands:
echo   git checkout -b feature/your-feature  # Create feature branch
echo   git add . ^&^& git commit -m "feat: ..." # Commit changes
echo   git push origin feature/your-feature   # Push to GitHub
echo   gh pr create                           # Create pull request
echo.
echo Documentation:
echo   - GIT_SETUP_GUIDE.md - Complete setup guide
echo   - CONTRIBUTING.md - Contribution guidelines
echo   - PROFESSIONAL_GIT_SETUP_SUMMARY.md - Quick reference
echo.
echo Happy coding! 🚀
echo.
pause
