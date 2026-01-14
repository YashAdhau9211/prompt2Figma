@echo off
REM Prompt2Figma Environment Setup Script for Windows
REM This script helps you set up environment variables for deployment

echo.
echo 🚀 Prompt2Figma Environment Setup
echo ==================================
echo.

REM Check if .env file exists
if exist "prompt2Figma-Backend\.env" (
    echo ⚠️  .env file already exists. Do you want to overwrite it? (y/n)
    set /p response=
    if not "!response!"=="y" (
        echo Exiting without changes.
        exit /b 0
    )
)

REM Get Gemini API Key
echo 📝 Enter your Google Gemini API Key:
echo    (Get it from: https://makersuite.google.com/app/apikey)
set /p GEMINI_KEY=

if "%GEMINI_KEY%"=="" (
    echo ❌ API key is required!
    exit /b 1
)

REM Ask for deployment type
echo.
echo 🌐 Where are you deploying?
echo    1) Local development (localhost)
echo    2) Railway.app
echo    3) Render.com
echo    4) Other (custom Redis URL)
set /p DEPLOY_TYPE=

REM Set Redis URLs based on deployment type
if "%DEPLOY_TYPE%"=="1" (
    set REDIS_BROKER=redis://localhost:6379/0
    set REDIS_RESULT=redis://localhost:6379/0
    set REDIS_STATE=redis://localhost:6379/1
    echo ✅ Using local Redis
) else if "%DEPLOY_TYPE%"=="2" (
    set REDIS_BROKER=redis://redis:6379/0
    set REDIS_RESULT=redis://redis:6379/0
    set REDIS_STATE=redis://redis:6379/1
    echo ✅ Using Railway Redis (internal URL)
) else if "%DEPLOY_TYPE%"=="3" (
    echo 📝 Enter your Render Redis internal URL:
    set /p REDIS_URL=
    set REDIS_BROKER=%REDIS_URL%/0
    set REDIS_RESULT=%REDIS_URL%/0
    set REDIS_STATE=%REDIS_URL%/1
) else if "%DEPLOY_TYPE%"=="4" (
    echo 📝 Enter your Redis URL:
    set /p REDIS_URL=
    set REDIS_BROKER=%REDIS_URL%/0
    set REDIS_RESULT=%REDIS_URL%/0
    set REDIS_STATE=%REDIS_URL%/1
) else (
    echo ❌ Invalid option!
    exit /b 1
)

REM Create .env file
(
echo # Celery Configuration
echo CELERY_BROKER_URL=%REDIS_BROKER%
echo CELERY_RESULT_BACKEND=%REDIS_RESULT%
echo.
echo # Redis State Store
echo REDIS_STATE_STORE_URL=%REDIS_STATE%
echo.
echo # Google Gemini API Key
echo GEMINI_API_KEY=%GEMINI_KEY%
) > "prompt2Figma-Backend\.env"

echo.
echo ✅ Environment file created successfully!
echo.
echo 📁 Location: prompt2Figma-Backend\.env
echo.
echo ⚠️  IMPORTANT: Never commit this file to Git!
echo    It's already in .gitignore
echo.
echo Next steps:
echo 1. Start Redis (if local): redis-server
echo 2. Start backend: cd prompt2Figma-Backend ^&^& uvicorn app.main:app --reload
echo 3. Start worker: cd prompt2Figma-Backend ^&^& celery -A app.tasks.celery_app worker --loglevel=info
echo.
pause
