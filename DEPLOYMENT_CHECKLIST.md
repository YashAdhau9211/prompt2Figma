# ✅ Deployment Checklist

Use this checklist to track your deployment progress.

---

## Phase 1: Preparation

### Get API Key
- [ ] Visit https://makersuite.google.com/app/apikey
- [ ] Sign in with Google account
- [ ] Create API key
- [ ] Copy and save API key securely
- [ ] Test API key (optional)

### Choose Hosting Platform
- [ ] Review options (Railway, Render, Fly.io)
- [ ] Sign up for chosen platform
- [ ] Connect GitHub account
- [ ] Verify free tier availability

---

## Phase 2: Backend Deployment

### Deploy Web Service
- [ ] Create new project/service
- [ ] Connect GitHub repository
- [ ] Select `prompt2Figma-Backend` directory
- [ ] Configure build settings
- [ ] Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Wait for initial deployment

### Add Redis Database
- [ ] Create Redis instance
- [ ] Note Redis connection URL
- [ ] Verify Redis is running
- [ ] Test Redis connection

### Deploy Celery Worker
- [ ] Create worker service
- [ ] Connect same repository
- [ ] Set start command: `celery -A app.tasks.celery_app worker --loglevel=info`
- [ ] Configure same environment variables
- [ ] Verify worker is running

### Configure Environment Variables
- [ ] Set `GEMINI_API_KEY`
- [ ] Set `CELERY_BROKER_URL`
- [ ] Set `CELERY_RESULT_BACKEND`
- [ ] Set `REDIS_STATE_STORE_URL`
- [ ] Verify all variables are set correctly

### Test Backend
- [ ] Get backend URL from platform
- [ ] Visit `https://your-app.railway.app` in browser
- [ ] Check health endpoint: `https://your-app.railway.app/health`
- [ ] Check API docs: `https://your-app.railway.app/docs`
- [ ] Test a simple API call (optional)

---

## Phase 3: Plugin Configuration

### Update Backend URL
- [ ] Open `prompt2Figma-Frontend (Plugin)/src/ui/ui.js`
- [ ] Find line 830: `const backendUrl = "http://localhost:8000";`
- [ ] Replace with your backend URL: `const backendUrl = "https://your-app.railway.app";`
- [ ] Save file

### Update Network Access
- [ ] Open `prompt2Figma-Frontend (Plugin)/manifest.json`
- [ ] Add `networkAccess` section if not present
- [ ] Add your backend domain to `allowedDomains`
- [ ] Add `generativelanguage.googleapis.com` to `allowedDomains`
- [ ] Save file

### Build Plugin
- [ ] Open terminal/command prompt
- [ ] Navigate to plugin directory: `cd "prompt2Figma-Frontend (Plugin)"`
- [ ] Install dependencies: `npm install`
- [ ] Build plugin: `npm run build`
- [ ] Verify `dist/` folder is created
- [ ] Check for build errors

---

## Phase 4: Testing

### Test in Figma Desktop
- [ ] Open Figma Desktop App
- [ ] Go to Plugins → Development → Import plugin from manifest
- [ ] Select `manifest.json` from plugin folder
- [ ] Plugin appears in development plugins list

### Test Basic Functionality
- [ ] Open plugin from Plugins menu
- [ ] Plugin UI loads correctly
- [ ] No console errors (check DevTools)

### Test Wireframe Generation
- [ ] Enter test prompt: "Create a login form"
- [ ] Click "Generate Wireframe"
- [ ] Backend connection successful
- [ ] Wireframe appears on canvas
- [ ] No errors in console

### Test Different Prompts
- [ ] Test mobile layout: "Create a mobile app dashboard"
- [ ] Test desktop layout: "Create a desktop analytics dashboard"
- [ ] Test dark mode: "Create a dark mode settings page"
- [ ] Test complex prompt: "Create a dashboard with sidebar, header, and charts"

### Test Error Handling
- [ ] Test with empty prompt
- [ ] Test with very long prompt
- [ ] Test with special characters
- [ ] Verify error messages are clear

---

## Phase 5: Prepare for Publishing

### Create Plugin Assets
- [ ] Design plugin icon (128x128px)
- [ ] Save as `icon.png` in plugin folder
- [ ] Create cover image (1920x960px)
- [ ] Take screenshots of plugin in action
- [ ] Take screenshots of generated wireframes

### Update Plugin Metadata
- [ ] Review `manifest.json`
- [ ] Verify plugin name
- [ ] Verify plugin ID
- [ ] Verify network access domains
- [ ] Add plugin icon reference (if needed)

### Write Plugin Description
- [ ] Write compelling tagline (< 60 characters)
- [ ] Write detailed description (< 500 words)
- [ ] List key features
- [ ] Add usage instructions
- [ ] Mention AI-powered capabilities

### Choose Tags
- [ ] Select relevant tags (AI, wireframe, design, etc.)
- [ ] Choose appropriate category (Productivity)
- [ ] Add keywords for search

---

## Phase 6: Publishing

### Publish to Figma Community
- [ ] In Figma Desktop: Plugins → Development → Your Plugin
- [ ] Click "Publish" button
- [ ] Fill in plugin name
- [ ] Add tagline
- [ ] Add description
- [ ] Upload icon
- [ ] Upload cover image
- [ ] Upload screenshots
- [ ] Add tags
- [ ] Choose category

### Choose Visibility
- [ ] Public (anyone can install - requires review)
- [ ] Organization only (private - no review)

### Submit for Review (if public)
- [ ] Review all information
- [ ] Submit for Figma team review
- [ ] Wait for approval (1-2 weeks)
- [ ] Check email for updates

---

## Phase 7: Post-Deployment

### Set Up Monitoring
- [ ] Set up uptime monitoring (UptimeRobot)
- [ ] Configure error tracking (Sentry)
- [ ] Set up log aggregation (Better Stack)
- [ ] Configure alerts for downtime

### Monitor Usage
- [ ] Check backend logs regularly
- [ ] Monitor API quota usage
- [ ] Track plugin installs (if public)
- [ ] Monitor error rates

### Share Plugin
- [ ] Get plugin URL from Figma Community
- [ ] Share on social media (Twitter, LinkedIn)
- [ ] Post in design communities
- [ ] Share with colleagues/friends
- [ ] Add to portfolio

### Documentation
- [ ] Update README with deployment info
- [ ] Document any issues encountered
- [ ] Create troubleshooting guide
- [ ] Write usage tutorial (optional)

---

## Phase 8: Maintenance

### Weekly Tasks
- [ ] Check backend uptime
- [ ] Review error logs
- [ ] Monitor API quota usage
- [ ] Check for user feedback

### Monthly Tasks
- [ ] Update dependencies
- [ ] Check for security updates
- [ ] Review usage patterns
- [ ] Analyze costs
- [ ] Plan improvements

### As Needed
- [ ] Fix reported bugs
- [ ] Add requested features
- [ ] Optimize performance
- [ ] Scale resources if needed
- [ ] Upgrade to paid tier if needed

---

## Troubleshooting Checklist

### If Plugin Can't Connect to Backend
- [ ] Verify backend URL in `ui.js` is correct
- [ ] Check backend is running (visit URL in browser)
- [ ] Verify HTTPS (not HTTP)
- [ ] Check network access in `manifest.json`
- [ ] Check CORS settings in backend
- [ ] Review browser console for errors

### If Gemini API Errors
- [ ] Verify API key is correct
- [ ] Check API key is set in environment variables
- [ ] Check rate limits (60/min, 1500/day)
- [ ] Wait and retry if rate limited
- [ ] Check Google Cloud Console for quota

### If Backend Not Deploying
- [ ] Check deployment logs
- [ ] Verify all environment variables are set
- [ ] Check Redis connection
- [ ] Verify Python version (3.9+)
- [ ] Check for dependency errors
- [ ] Review platform-specific docs

### If Plugin Not Rendering
- [ ] Check Figma DevTools console
- [ ] Verify JSON structure from backend
- [ ] Test with simple prompt first
- [ ] Rebuild plugin: `npm run build`
- [ ] Check for JavaScript errors
- [ ] Verify backend returns valid JSON

---

## Success Criteria

### Backend
- ✅ Backend is deployed and accessible
- ✅ Health check returns 200 OK
- ✅ API docs are accessible
- ✅ Redis is connected
- ✅ Celery worker is running
- ✅ No errors in logs

### Plugin
- ✅ Plugin loads in Figma
- ✅ UI displays correctly
- ✅ Connects to backend successfully
- ✅ Generates wireframes correctly
- ✅ No console errors
- ✅ Handles errors gracefully

### Publishing
- ✅ Plugin is published to Figma Community
- ✅ Plugin is discoverable by search
- ✅ Users can install with one click
- ✅ Plugin works for all users
- ✅ Positive user feedback

### Monitoring
- ✅ Uptime monitoring is active
- ✅ Error tracking is configured
- ✅ Logs are accessible
- ✅ Alerts are set up
- ✅ Usage metrics are tracked

---

## Completion Status

**Overall Progress**: _____ / 100%

**Phase 1 - Preparation**: _____ / 100%
**Phase 2 - Backend Deployment**: _____ / 100%
**Phase 3 - Plugin Configuration**: _____ / 100%
**Phase 4 - Testing**: _____ / 100%
**Phase 5 - Prepare for Publishing**: _____ / 100%
**Phase 6 - Publishing**: _____ / 100%
**Phase 7 - Post-Deployment**: _____ / 100%
**Phase 8 - Maintenance**: _____ / 100%

---

## Notes

Use this section to track issues, decisions, or important information:

```
Date: ___________
Backend URL: ___________
Platform: ___________
Plugin URL: ___________

Issues Encountered:
-
-
-

Solutions Applied:
-
-
-

Next Steps:
-
-
-
```

---

## Quick Reference

### Important URLs
- Backend: `https://your-app.railway.app`
- Health Check: `https://your-app.railway.app/health`
- API Docs: `https://your-app.railway.app/docs`
- Plugin: `https://www.figma.com/community/plugin/your-plugin-id`

### Important Files
- Backend URL: `prompt2Figma-Frontend (Plugin)/src/ui/ui.js` (line 830)
- Network Access: `prompt2Figma-Frontend (Plugin)/manifest.json`
- Environment: `prompt2Figma-Backend/.env`

### Important Commands
```bash
# Build plugin
cd "prompt2Figma-Frontend (Plugin)"
npm run build

# Configure plugin (automated)
node configure-plugin.js

# Setup environment (automated)
./setup-env.sh  # or setup-env.bat on Windows
```

---

**Good luck with your deployment! 🚀**
