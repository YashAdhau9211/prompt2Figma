# 🚀 Quick Start - Deploy Prompt2Figma for Free

This guide will get you up and running in **under 30 minutes**.

## What You'll Need

- [ ] GitHub account (free)
- [ ] Google account (for Gemini API - free)
- [ ] Figma account (free)
- [ ] Railway/Render account (free)

---

## Step 1: Get Google Gemini API Key (5 minutes)

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIzaSy...`)
5. Save it somewhere safe

**Free Tier:** 60 requests/minute, 1,500 requests/day

---

## Step 2: Deploy Backend to Railway (10 minutes)

### Option A: One-Click Deploy (Easiest)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

1. Click the button above
2. Sign in with GitHub
3. Select this repository
4. Railway will create:
   - Web service (FastAPI)
   - Redis database
   - Celery worker

5. Add environment variables:
   - Go to your project → Variables
   - Add these:
     ```
     GEMINI_API_KEY=your_key_from_step_1
     CELERY_BROKER_URL=redis://redis:6379/0
     CELERY_RESULT_BACKEND=redis://redis:6379/0
     REDIS_STATE_STORE_URL=redis://redis:6379/1
     ```

6. Wait for deployment (2-3 minutes)

7. Copy your backend URL:
   - Go to Settings → Domains
   - Copy the URL (e.g., `https://your-app.railway.app`)

### Option B: Manual Deploy

1. Go to https://railway.app
2. Sign up with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your forked repository
5. Add **Redis** database:
   - Click **"New"** → **"Database"** → **"Add Redis"**
6. Add **Celery Worker**:
   - Click **"New"** → **"Empty Service"**
   - Connect same repo
   - Set start command: `celery -A app.tasks.celery_app worker --loglevel=info`
7. Set environment variables (same as above)
8. Deploy and copy URL

---

## Step 3: Configure Plugin (5 minutes)

### Automatic Configuration (Recommended)

```bash
# Run the configuration script
node configure-plugin.js

# Enter your Railway URL when prompted
# Example: https://your-app.railway.app
```

### Manual Configuration

1. Open `prompt2Figma-Frontend (Plugin)/src/ui/ui.js`

2. Find line 830 and update:
   ```javascript
   // Change this:
   const backendUrl = "http://localhost:8000";
   
   // To your Railway URL:
   const backendUrl = "https://your-app.railway.app";
   ```

3. Open `prompt2Figma-Frontend (Plugin)/manifest.json`

4. Add network access:
   ```json
   {
     "name": "Prompt2Figma",
     "networkAccess": {
       "allowedDomains": [
         "your-app.railway.app",
         "generativelanguage.googleapis.com"
       ]
     }
   }
   ```

---

## Step 4: Build Plugin (2 minutes)

```bash
cd "prompt2Figma-Frontend (Plugin)"
npm install
npm run build
```

This creates the `dist/` folder with your compiled plugin.

---

## Step 5: Test Plugin in Figma (5 minutes)

1. Open **Figma Desktop App** (download from https://figma.com/downloads)

2. Go to **Plugins** → **Development** → **Import plugin from manifest**

3. Select `prompt2Figma-Frontend (Plugin)/manifest.json`

4. Run the plugin:
   - Right-click on canvas
   - Plugins → Development → Prompt2Figma

5. Test with a prompt:
   ```
   Create a login form with email, password, and a submit button
   ```

6. If it works, you'll see a wireframe appear on your canvas! 🎉

---

## Step 6: Publish to Figma Community (5 minutes)

### Prepare Assets

1. **Create Plugin Icon** (128x128px)
   - Simple, recognizable design
   - Save as `icon.png` in plugin folder

2. **Take Screenshots**
   - Show plugin UI
   - Show generated wireframes
   - Show different use cases

### Publish

1. In Figma Desktop:
   - Plugins → Development → Your Plugin
   - Click **"Publish"**

2. Fill in details:
   - **Name**: Prompt2Figma
   - **Tagline**: AI-powered wireframe generation from text prompts
   - **Description**: 
     ```
     Transform your ideas into Figma wireframes instantly using AI. 
     Simply describe your UI in natural language, and Prompt2Figma 
     will generate professional wireframes on your canvas.
     
     Features:
     • Natural language to wireframe conversion
     • Mobile and desktop layouts
     • Dark and light mode support
     • Iterative design refinement
     • React code generation
     ```
   - **Tags**: AI, wireframe, design, automation, prototyping, productivity
   - **Category**: Productivity

3. Upload assets:
   - Plugin icon
   - Cover image (1920x960px)
   - Screenshots

4. Choose visibility:
   - **Public**: Anyone can install (requires Figma review)
   - **Organization**: Only your team (no review needed)

5. Submit for review (if public)
   - Review takes 1-2 weeks
   - You'll get email notification

---

## Step 7: Share Your Plugin

### Get Plugin URL

After publishing, you'll get a URL like:
```
https://www.figma.com/community/plugin/your-plugin-id/prompt2figma
```

### Share Options

1. **Direct Link**: Share the URL
2. **Figma Community**: Users can search "Prompt2Figma"
3. **Social Media**: Share screenshots and demos
4. **GitHub**: Add badge to your README

---

## Troubleshooting

### Plugin Can't Connect to Backend

**Check:**
- [ ] Backend URL is correct in `ui.js`
- [ ] Backend is running (visit URL in browser)
- [ ] URL uses HTTPS (not HTTP)
- [ ] Network access is configured in `manifest.json`

**Test Backend:**
```bash
# Visit in browser:
https://your-app.railway.app/health

# Should return:
{
  "status": "healthy",
  "timestamp": "2026-01-14T...",
  "service": "prompt2figma-api"
}
```

### Gemini API Errors

**Check:**
- [ ] API key is correct
- [ ] Not exceeding rate limits (60/min, 1500/day)
- [ ] API key has Gemini API enabled

**Test API Key:**
```bash
curl -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### Plugin Not Rendering

**Check:**
- [ ] Plugin is built (`npm run build`)
- [ ] Figma DevTools console for errors (Plugins → Development → Open Console)
- [ ] Backend returns valid JSON
- [ ] Try simple prompt first: "Create a button"

### Railway/Render Issues

**Check:**
- [ ] All environment variables are set
- [ ] Redis is connected
- [ ] Celery worker is running
- [ ] Check deployment logs

---

## Monitoring Your Deployment

### Check Backend Health

```bash
# Health check
curl https://your-app.railway.app/health

# API docs
https://your-app.railway.app/docs
```

### View Logs

**Railway:**
- Project → Service → Logs tab

**Render:**
- Dashboard → Service → Logs

### Monitor Usage

**Railway:**
- Project → Usage tab
- Shows requests, bandwidth, compute time

**Google Gemini:**
- https://console.cloud.google.com
- APIs & Services → Gemini API → Quotas

---

## Cost Breakdown

### Free Tier (What You Get)

| Service | Free Tier | Limits |
|---------|-----------|--------|
| Railway | $5 credit/month | ~500 hours, sleeps after inactivity |
| Render | 750 hours/month | Sleeps after 15 min inactivity |
| Google Gemini | 1,500 requests/day | 60 requests/minute |
| Figma Plugin | Unlimited | Free to publish and use |

**Total Cost: $0/month** ✅

### When You'll Need to Upgrade

- More than 500 active users/day
- Need 24/7 uptime (no cold starts)
- Exceed 1,500 Gemini requests/day
- Want faster response times

**Paid Options:**
- Railway: $5-20/month
- Render: $7/month
- Google Gemini: Pay-as-you-go

---

## Next Steps

### Enhance Your Plugin

1. **Add Features**
   - Custom color schemes
   - Component library integration
   - Export to different formats

2. **Improve UX**
   - Better error messages
   - Loading animations
   - Undo/redo functionality

3. **Optimize Performance**
   - Cache common prompts
   - Reduce API calls
   - Optimize rendering

### Grow Your User Base

1. **Marketing**
   - Post on Twitter/LinkedIn
   - Share on design communities
   - Create tutorial videos

2. **Gather Feedback**
   - Add feedback form
   - Monitor user reviews
   - Iterate based on feedback

3. **Build Community**
   - Create Discord server
   - Share tips and tricks
   - Showcase user creations

---

## Support

### Resources

- **Documentation**: See `DEPLOYMENT_GUIDE.md` for detailed info
- **API Docs**: `https://your-app.railway.app/docs`
- **Figma Plugin API**: https://www.figma.com/plugin-docs/

### Get Help

- **Backend Issues**: Check Railway/Render logs
- **Plugin Issues**: Check Figma DevTools console
- **API Issues**: Check Google Cloud Console
- **General Questions**: Open GitHub issue

---

## Success Checklist

- [ ] Backend deployed and healthy
- [ ] Gemini API key working
- [ ] Plugin configured with backend URL
- [ ] Plugin built successfully
- [ ] Tested in Figma Desktop
- [ ] Plugin published to Figma Community
- [ ] Monitoring set up
- [ ] Shared with users

**Congratulations! Your plugin is live! 🎉**

---

## Example Prompts to Try

Once your plugin is working, try these prompts:

1. **Simple**
   ```
   Create a login form
   ```

2. **Detailed**
   ```
   Create a mobile app dashboard with a header, 
   three stat cards, and a list of recent activities
   ```

3. **Complex**
   ```
   Design a desktop analytics dashboard with a sidebar navigation,
   top bar with user profile, and main content area with charts
   ```

4. **Specific**
   ```
   Create a dark mode settings page with toggle switches,
   profile picture, and save button
   ```

---

**Ready to deploy? Start with Step 1! 🚀**
