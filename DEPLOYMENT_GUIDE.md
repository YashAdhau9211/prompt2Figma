# Prompt2Figma - Free Deployment Guide

## Overview
This guide will help you deploy the Prompt2Figma backend for free and publish the Figma plugin so anyone can use it.

## Architecture
- **Backend**: FastAPI + Celery + Redis (needs to be hosted)
- **Frontend**: Figma Plugin (published to Figma Community)
- **AI**: Google Gemini API (free tier available)

---

## Part 1: Backend Deployment (Free Options)

### Option A: Railway.app (Recommended - Easiest)

**Why Railway?**
- $5 free credit monthly (enough for small-scale usage)
- Built-in Redis support
- Easy deployment from GitHub
- Automatic HTTPS

**Steps:**

1. **Prepare Your Repository**
   ```bash
   # Create a Procfile in prompt2Figma-Backend/
   echo "web: uvicorn app.main:app --host 0.0.0.0 --port $PORT" > prompt2Figma-Backend/Procfile
   echo "worker: celery -A app.tasks.celery_app worker --loglevel=info" >> prompt2Figma-Backend/Procfile
   ```

2. **Sign up for Railway**
   - Go to https://railway.app
   - Sign up with GitHub (free)

3. **Deploy Backend**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect Python
   - Add these environment variables:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     CELERY_BROKER_URL=redis://redis:6379/0
     CELERY_RESULT_BACKEND=redis://redis:6379/0
     REDIS_STATE_STORE_URL=redis://redis:6379/1
     PORT=8000
     ```

4. **Add Redis Service**
   - In your Railway project, click "New" → "Database" → "Add Redis"
   - Railway will automatically link it

5. **Deploy Celery Worker**
   - Click "New" → "Empty Service"
   - Connect same GitHub repo
   - Set start command: `celery -A app.tasks.celery_app worker --loglevel=info`
   - Use same environment variables

6. **Get Your Backend URL**
   - Railway will provide a URL like: `https://your-app.railway.app`
   - Save this URL for the plugin configuration

---

### Option B: Render.com (Alternative Free Option)

**Why Render?**
- Free tier available (with limitations)
- Supports background workers
- Easy Redis integration

**Steps:**

1. **Sign up for Render**
   - Go to https://render.com
   - Sign up with GitHub (free)

2. **Create Redis Instance**
   - Dashboard → "New" → "Redis"
   - Choose free tier
   - Note the internal Redis URL

3. **Deploy Web Service**
   - Dashboard → "New" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Root Directory**: `prompt2Figma-Backend`
     - **Build Command**: `pip install -r requirements.txt && npm install`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     CELERY_BROKER_URL=your_redis_internal_url
     CELERY_RESULT_BACKEND=your_redis_internal_url
     REDIS_STATE_STORE_URL=your_redis_internal_url
     ```

4. **Deploy Celery Worker**
   - Dashboard → "New" → "Background Worker"
   - Same repository and root directory
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `celery -A app.tasks.celery_app worker --loglevel=info`
   - Same environment variables

5. **Get Your Backend URL**
   - Render provides: `https://your-app.onrender.com`

---

### Option C: Fly.io (Most Flexible)

**Why Fly.io?**
- Generous free tier
- Global deployment
- Docker-based (more control)

**Steps:**

1. **Install Fly CLI**
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   
   # Or download from https://fly.io/docs/hands-on/install-flyctl/
   ```

2. **Sign up and Login**
   ```bash
   fly auth signup
   fly auth login
   ```

3. **Create Dockerfile** (in prompt2Figma-Backend/)
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   # Install Node.js for AST validation
   RUN apt-get update && apt-get install -y nodejs npm && rm -rf /var/lib/apt/lists/*
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY package*.json ./
   RUN npm install
   
   COPY . .
   
   EXPOSE 8000
   
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

4. **Deploy**
   ```bash
   cd prompt2Figma-Backend
   fly launch
   # Follow prompts, choose free tier
   
   # Set environment variables
   fly secrets set GEMINI_API_KEY=your_key_here
   fly secrets set CELERY_BROKER_URL=redis://your-redis-url
   fly secrets set CELERY_RESULT_BACKEND=redis://your-redis-url
   fly secrets set REDIS_STATE_STORE_URL=redis://your-redis-url
   ```

5. **Add Redis**
   ```bash
   fly redis create
   # Note the connection URL
   ```

---

## Part 2: Get Free Google Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)
5. Free tier includes:
   - 60 requests per minute
   - 1,500 requests per day
   - Sufficient for personal/small team use

---

## Part 3: Update Plugin Configuration

### Update Backend URL in Plugin

1. **Edit the plugin UI file**:


   Open `prompt2Figma-Frontend (Plugin)/src/ui/ui.js`
   
   Find line 830 and replace with your deployed backend URL:
   ```javascript
   // OLD:
   const backendUrl = "http://localhost:8000";
   
   // NEW (use your Railway/Render/Fly.io URL):
   const backendUrl = "https://your-app.railway.app";
   ```

2. **Rebuild the plugin**:
   ```bash
   cd "prompt2Figma-Frontend (Plugin)"
   npm install
   npm run build
   ```

---

## Part 4: Publish Figma Plugin

### Prerequisites
- Figma account (free)
- Plugin must be tested and working
- Plugin icon/cover image (optional but recommended)

### Steps to Publish

1. **Test Your Plugin Locally First**
   - Open Figma Desktop App
   - Go to Plugins → Development → Import plugin from manifest
   - Select `prompt2Figma-Frontend (Plugin)/manifest.json`
   - Test thoroughly with your deployed backend

2. **Prepare Plugin Assets**
   
   Create a plugin icon (128x128px):
   - Design a simple icon representing your plugin
   - Export as PNG
   - Save as `icon.png` in plugin folder

3. **Update manifest.json**
   
   Edit `prompt2Figma-Frontend (Plugin)/manifest.json`:
   ```json
   {
     "name": "Prompt2Figma",
     "id": "prompt2figma",
     "api": "1.0.0",
     "main": "dist/code.js",
     "ui": "dist/ui.html",
     "editorType": ["figma"],
     "menu": [
       {
         "name": "Prompt2Figma",
         "command": "run"
       }
     ],
     "documentAccess": "dynamic-page",
     "networkAccess": {
       "allowedDomains": [
         "your-app.railway.app",
         "generativelanguage.googleapis.com"
       ]
     }
   }
   ```

4. **Publish to Figma Community**
   
   **Option A: Publish Publicly (Anyone can use)**
   - In Figma, go to Plugins → Development → Your Plugin
   - Click "Publish" button
   - Fill in details:
     - **Name**: Prompt2Figma
     - **Description**: AI-powered plugin that transforms natural language prompts into interactive UI wireframes
     - **Tags**: AI, wireframe, design, automation, prototyping
     - **Cover Image**: Upload a screenshot of your plugin in action
   - Choose "Public" visibility
   - Submit for review (Figma team reviews within 1-2 weeks)

   **Option B: Publish as Organization Plugin (Private)**
   - Same steps but choose "Organization only"
   - Share link with specific users
   - No review needed

5. **Share Your Plugin**
   - Once approved, you'll get a Figma Community URL
   - Share: `https://www.figma.com/community/plugin/your-plugin-id`
   - Users can install with one click

---

## Part 5: Cost Optimization & Scaling

### Free Tier Limitations

**Railway.app:**
- $5/month credit (≈500 hours)
- Good for: 100-500 requests/day
- Sleeps after inactivity (cold starts)

**Render.com:**
- Free tier: 750 hours/month
- Sleeps after 15 min inactivity
- Good for: 50-200 requests/day

**Google Gemini:**
- 60 requests/minute
- 1,500 requests/day
- Good for: Small teams

### When You Need to Scale (Paid Options)

**If you exceed free tiers:**

1. **Railway**: $5-20/month for more resources
2. **Render**: $7/month for always-on service
3. **DigitalOcean**: $6/month for basic droplet
4. **AWS/GCP**: Pay-as-you-go (can be expensive)

### Cost-Saving Tips

1. **Implement Caching**
   - Cache common prompts in Redis
   - Reduce API calls to Gemini

2. **Rate Limiting**
   - Already implemented in your backend
   - Prevents abuse

3. **Optimize Celery**
   - Use single worker on free tier
   - Scale workers only when needed

4. **Monitor Usage**
   - Track API calls
   - Set up alerts for quota limits

---

## Part 6: Maintenance & Monitoring

### Health Checks

Add to your backend (`app/main.py`):
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
```

### Monitoring Tools (Free)

1. **UptimeRobot** (https://uptimerobot.com)
   - Monitor backend uptime
   - Email alerts on downtime
   - Free: 50 monitors

2. **Better Stack** (https://betterstack.com)
   - Log aggregation
   - Error tracking
   - Free tier available

3. **Sentry** (https://sentry.io)
   - Error tracking
   - Performance monitoring
   - Free: 5K events/month

---

## Part 7: Security Best Practices

### Before Going Public

1. **Secure Your API Key**
   - Never commit `.env` file
   - Use environment variables only
   - Rotate keys regularly

2. **Add Rate Limiting**
   - Already implemented in your code
   - Consider per-user limits

3. **CORS Configuration**
   - Update `app/main.py` to restrict origins:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "https://www.figma.com",
           "https://figma.com"
       ],
       allow_credentials=True,
       allow_methods=["POST", "GET"],
       allow_headers=["*"],
   )
   ```

4. **Input Validation**
   - Already implemented with Pydantic
   - Add max prompt length checks

5. **HTTPS Only**
   - All free hosting options provide HTTPS
   - Never use HTTP in production

---

## Part 8: Quick Start Checklist

### Backend Deployment
- [ ] Sign up for Railway/Render/Fly.io
- [ ] Get Google Gemini API key
- [ ] Deploy backend service
- [ ] Deploy Celery worker
- [ ] Add Redis instance
- [ ] Set environment variables
- [ ] Test backend health endpoint
- [ ] Note your backend URL

### Plugin Configuration
- [ ] Update `backendUrl` in `ui.js`
- [ ] Update `manifest.json` with network access
- [ ] Rebuild plugin (`npm run build`)
- [ ] Test plugin locally
- [ ] Create plugin icon
- [ ] Prepare screenshots

### Publishing
- [ ] Test plugin thoroughly
- [ ] Submit to Figma Community
- [ ] Wait for approval (1-2 weeks)
- [ ] Share plugin link
- [ ] Monitor usage and errors

---

## Part 9: Troubleshooting

### Common Issues

**1. Plugin can't connect to backend**
- Check backend URL in `ui.js`
- Verify backend is running (visit URL in browser)
- Check CORS settings
- Ensure HTTPS (not HTTP)

**2. Gemini API errors**
- Verify API key is correct
- Check quota limits (60/min, 1500/day)
- Wait and retry if rate limited

**3. Redis connection errors**
- Verify Redis URL in environment variables
- Check Redis instance is running
- Ensure internal URLs are used (not external)

**4. Celery worker not processing**
- Check worker logs
- Verify Redis connection
- Restart worker service

**5. Plugin not rendering**
- Check browser console for errors
- Verify JSON structure from backend
- Test with simple prompts first

### Getting Help

- **Backend Issues**: Check Railway/Render logs
- **Plugin Issues**: Check Figma DevTools console
- **API Issues**: Check Google Cloud Console

---

## Part 10: Example Deployment (Railway)

Here's a complete example using Railway:

### Step-by-Step

1. **Fork/Clone Repository**
   ```bash
   git clone https://github.com/your-username/prompt2figma.git
   cd prompt2figma
   ```

2. **Get Gemini API Key**
   - Visit https://makersuite.google.com/app/apikey
   - Create key, copy it

3. **Deploy to Railway**
   - Go to https://railway.app
   - New Project → Deploy from GitHub
   - Select your repo
   - Add Redis database
   - Set environment variables:
     ```
     GEMINI_API_KEY=AIzaSy...your-key
     CELERY_BROKER_URL=redis://redis:6379/0
     CELERY_RESULT_BACKEND=redis://redis:6379/0
     REDIS_STATE_STORE_URL=redis://redis:6379/1
     ```

4. **Add Celery Worker**
   - New Service → Same repo
   - Custom start command: `celery -A app.tasks.celery_app worker --loglevel=info`
   - Same environment variables

5. **Get Backend URL**
   - Railway provides: `https://prompt2figma-production.up.railway.app`

6. **Update Plugin**
   ```bash
   cd "prompt2Figma-Frontend (Plugin)"
   
   # Edit src/ui/ui.js line 830:
   # const backendUrl = "https://prompt2figma-production.up.railway.app";
   
   npm install
   npm run build
   ```

7. **Test Plugin**
   - Open Figma Desktop
   - Plugins → Development → Import plugin from manifest
   - Test with prompt: "Create a login form"

8. **Publish**
   - In Figma: Plugins → Development → Publish
   - Fill in details, submit

**Done!** Your plugin is now live and anyone can use it.

---

## Summary

**Total Cost: $0/month** (within free tiers)

**What You Get:**
- ✅ Deployed backend API
- ✅ Redis for state management
- ✅ Celery for async tasks
- ✅ AI-powered wireframe generation
- ✅ Published Figma plugin
- ✅ HTTPS security
- ✅ Monitoring and logs

**Limitations:**
- ~100-500 requests/day (free tier)
- Cold starts after inactivity
- 1,500 Gemini API calls/day

**When to Upgrade:**
- More than 500 users/day
- Need 24/7 uptime
- Want faster response times
- Exceed API quotas

---

## Next Steps

1. Choose a hosting platform (Railway recommended)
2. Deploy backend following the guide
3. Update plugin with backend URL
4. Test thoroughly
5. Publish to Figma Community
6. Share with the world! 🚀

**Questions?** Check the troubleshooting section or open an issue on GitHub.
