#!/bin/bash

# Prompt2Figma Environment Setup Script
# This script helps you set up environment variables for deployment

echo "🚀 Prompt2Figma Environment Setup"
echo "=================================="
echo ""

# Check if .env file exists
if [ -f "prompt2Figma-Backend/.env" ]; then
    echo "⚠️  .env file already exists. Do you want to overwrite it? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        echo "Exiting without changes."
        exit 0
    fi
fi

# Get Gemini API Key
echo "📝 Enter your Google Gemini API Key:"
echo "   (Get it from: https://makersuite.google.com/app/apikey)"
read -r GEMINI_KEY

if [ -z "$GEMINI_KEY" ]; then
    echo "❌ API key is required!"
    exit 1
fi

# Ask for deployment type
echo ""
echo "🌐 Where are you deploying?"
echo "   1) Local development (localhost)"
echo "   2) Railway.app"
echo "   3) Render.com"
echo "   4) Other (custom Redis URL)"
read -r DEPLOY_TYPE

# Set Redis URLs based on deployment type
case $DEPLOY_TYPE in
    1)
        REDIS_BROKER="redis://localhost:6379/0"
        REDIS_RESULT="redis://localhost:6379/0"
        REDIS_STATE="redis://localhost:6379/1"
        echo "✅ Using local Redis"
        ;;
    2)
        REDIS_BROKER="redis://redis:6379/0"
        REDIS_RESULT="redis://redis:6379/0"
        REDIS_STATE="redis://redis:6379/1"
        echo "✅ Using Railway Redis (internal URL)"
        ;;
    3)
        echo "📝 Enter your Render Redis internal URL:"
        read -r REDIS_URL
        REDIS_BROKER="$REDIS_URL/0"
        REDIS_RESULT="$REDIS_URL/0"
        REDIS_STATE="$REDIS_URL/1"
        ;;
    4)
        echo "📝 Enter your Redis URL:"
        read -r REDIS_URL
        REDIS_BROKER="$REDIS_URL/0"
        REDIS_RESULT="$REDIS_URL/0"
        REDIS_STATE="$REDIS_URL/1"
        ;;
    *)
        echo "❌ Invalid option!"
        exit 1
        ;;
esac

# Create .env file
cat > "prompt2Figma-Backend/.env" << EOF
# Celery Configuration
CELERY_BROKER_URL=$REDIS_BROKER
CELERY_RESULT_BACKEND=$REDIS_RESULT

# Redis State Store
REDIS_STATE_STORE_URL=$REDIS_STATE

# Google Gemini API Key
GEMINI_API_KEY=$GEMINI_KEY
EOF

echo ""
echo "✅ Environment file created successfully!"
echo ""
echo "📁 Location: prompt2Figma-Backend/.env"
echo ""
echo "⚠️  IMPORTANT: Never commit this file to Git!"
echo "   It's already in .gitignore"
echo ""
echo "Next steps:"
echo "1. Start Redis (if local): redis-server"
echo "2. Start backend: cd prompt2Figma-Backend && uvicorn app.main:app --reload"
echo "3. Start worker: cd prompt2Figma-Backend && celery -A app.tasks.celery_app worker --loglevel=info"
echo ""
