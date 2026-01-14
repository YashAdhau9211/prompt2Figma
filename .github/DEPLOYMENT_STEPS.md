# 🚀 Deployment Steps - Visual Guide

## 5 Simple Steps to Deploy Prompt2Figma

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  STEP 1: GET API KEY                                    ⏱️ 5 min │
│  ═══════════════════                                              │
│                                                                   │
│  🌐 Visit: https://makersuite.google.com/app/apikey              │
│  👤 Sign in with Google                                          │
│  🔑 Click "Create API Key"                                       │
│  📋 Copy key (starts with AIzaSy...)                             │
│  💾 Save it securely                                             │
│                                                                   │
│  ✅ Free Tier: 1,500 requests/day                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  STEP 2: DEPLOY BACKEND                                ⏱️ 10 min │
│  ═══════════════════════                                          │
│                                                                   │
│  🌐 Visit: https://railway.app                                   │
│  👤 Sign up with GitHub                                          │
│  ➕ New Project → Deploy from GitHub                             │
│  📁 Select your repository                                       │
│  🗄️ Add Redis database                                           │
│  ⚙️ Set environment variables:                                   │
│     • GEMINI_API_KEY=your_key                                    │
│     • CELERY_BROKER_URL=redis://redis:6379/0                    │
│     • CELERY_RESULT_BACKEND=redis://redis:6379/0                │
│     • REDIS_STATE_STORE_URL=redis://redis:6379/1                │
│  🚀 Deploy!                                                      │
│  📋 Copy backend URL: https://your-app.railway.app               │
│                                                                   │
│  ✅ Free Tier: $5 credit/month                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  STEP 3: CONFIGURE PLUGIN                              ⏱️ 5 min  │
│  ═══════════════════════                                          │
│                                                                   │
│  Option A: Automatic (Recommended)                               │
│  ─────────────────────────────                                   │
│  💻 Run: node configure-plugin.js                                │
│  📝 Enter your backend URL                                       │
│  ✅ Done!                                                        │
│                                                                   │
│  Option B: Manual                                                │
│  ─────────────────                                               │
│  📝 Edit: prompt2Figma-Frontend (Plugin)/src/ui/ui.js           │
│  🔍 Find line 830                                                │
│  ✏️ Change: const backendUrl = "https://your-app.railway.app"   │
│  💾 Save file                                                    │
│                                                                   │
│  📝 Edit: prompt2Figma-Frontend (Plugin)/manifest.json          │
│  ➕ Add networkAccess section with your domain                   │
│  💾 Save file                                                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  STEP 4: BUILD & TEST                                  ⏱️ 7 min  │
│  ═══════════════════                                              │
│                                                                   │
│  Build Plugin:                                                   │
│  ─────────────                                                   │
│  💻 cd "prompt2Figma-Frontend (Plugin)"                          │
│  📦 npm install                                                  │
│  🔨 npm run build                                                │
│  ✅ Check dist/ folder created                                   │
│                                                                   │
│  Test in Figma:                                                  │
│  ──────────────                                                  │
│  🎨 Open Figma Desktop App                                       │
│  🔌 Plugins → Development → Import plugin from manifest          │
│  📁 Select manifest.json                                         │
│  ▶️ Run plugin                                                   │
│  📝 Test prompt: "Create a login form"                           │
│  ✅ Verify wireframe appears                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  STEP 5: PUBLISH                                       ⏱️ 5 min  │
│  ════════════════                                                 │
│                                                                   │
│  Prepare Assets:                                                 │
│  ───────────────                                                 │
│  🎨 Create plugin icon (128x128px)                               │
│  📸 Take screenshots                                             │
│  📝 Write description                                            │
│                                                                   │
│  Publish to Figma:                                               │
│  ─────────────────                                               │
│  🎨 Figma Desktop → Plugins → Development                        │
│  📤 Click "Publish"                                              │
│  📝 Fill in details:                                             │
│     • Name: Prompt2Figma                                         │
│     • Tagline: AI-powered wireframe generation                  │
│     • Description: Transform ideas into wireframes...            │
│     • Tags: AI, wireframe, design, automation                   │
│  🖼️ Upload icon and screenshots                                  │
│  🌍 Choose "Public" visibility                                   │
│  ✅ Submit for review                                            │
│                                                                   │
│  ⏳ Wait 1-2 weeks for approval                                  │
│  🎉 Share your plugin URL!                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

                              ⬇️

┌─────────────────────────────────────────────────────────────────┐
│                                                                   │
│  🎉 SUCCESS! YOUR PLUGIN IS LIVE!                                │
│  ═══════════════════════════════                                 │
│                                                                   │
│  ✅ Backend deployed and running                                 │
│  ✅ Plugin published to Figma Community                          │
│  ✅ Anyone can install and use it                                │
│  ✅ Total cost: $0/month                                         │
│                                                                   │
│  📊 What You Can Handle (Free Tier):                             │
│     • 100-500 users/day                                          │
│     • 1,500 AI requests/day                                      │
│     • ~500 hours uptime/month                                    │
│                                                                   │
│  🚀 Next Steps:                                                  │
│     1. Set up monitoring (UptimeRobot)                           │
│     2. Share on social media                                     │
│     3. Gather user feedback                                      │
│     4. Iterate and improve                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Quick Reference

### Important URLs

```
┌─────────────────────────────────────────────────────────────┐
│  Service          │  URL                                     │
├─────────────────────────────────────────────────────────────┤
│  Gemini API Key   │  https://makersuite.google.com/app/apikey│
│  Railway          │  https://railway.app                     │
│  Render           │  https://render.com                      │
│  Fly.io           │  https://fly.io                          │
│  Figma Desktop    │  https://figma.com/downloads             │
│  Your Backend     │  https://your-app.railway.app            │
│  Health Check     │  https://your-app.railway.app/health     │
│  API Docs         │  https://your-app.railway.app/docs       │
└─────────────────────────────────────────────────────────────┘
```

### Important Files

```
┌─────────────────────────────────────────────────────────────┐
│  File                                    │  What to Update   │
├─────────────────────────────────────────────────────────────┤
│  prompt2Figma-Backend/.env               │  API keys         │
│  prompt2Figma-Frontend/src/ui/ui.js     │  Backend URL      │
│  prompt2Figma-Frontend/manifest.json    │  Network access   │
└─────────────────────────────────────────────────────────────┘
```

### Important Commands

```bash
# Configure plugin (automatic)
node configure-plugin.js

# Setup environment (Windows)
setup-env.bat

# Setup environment (Linux/Mac)
./setup-env.sh

# Build plugin
cd "prompt2Figma-Frontend (Plugin)"
npm install
npm run build

# Test backend health
curl https://your-app.railway.app/health
```

---

## 🎯 Troubleshooting Quick Guide

```
┌─────────────────────────────────────────────────────────────┐
│  Problem                  │  Solution                        │
├─────────────────────────────────────────────────────────────┤
│  Plugin can't connect     │  • Check backend URL in ui.js   │
│  to backend               │  • Verify backend is running    │
│                           │  • Ensure HTTPS (not HTTP)      │
│                           │  • Check network access         │
├─────────────────────────────────────────────────────────────┤
│  Gemini API errors        │  • Verify API key is correct    │
│                           │  • Check rate limits            │
│                           │  • Wait and retry               │
├─────────────────────────────────────────────────────────────┤
│  Backend not deploying    │  • Check deployment logs        │
│                           │  • Verify env variables         │
│                           │  • Ensure Redis is connected    │
├─────────────────────────────────────────────────────────────┤
│  Plugin not rendering     │  • Check Figma DevTools         │
│                           │  • Rebuild plugin               │
│                           │  • Test with simple prompt      │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Cost Calculator

```
┌─────────────────────────────────────────────────────────────┐
│                    FREE TIER LIMITS                          │
├─────────────────────────────────────────────────────────────┤
│  Railway          │  $5 credit/month (~500 hours)           │
│  Google Gemini    │  1,500 requests/day                     │
│  Figma Plugin     │  Unlimited installs                     │
├─────────────────────────────────────────────────────────────┤
│  TOTAL COST       │  $0/month                               │
├─────────────────────────────────────────────────────────────┤
│  SUPPORTS         │  100-500 active users/day               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    WHEN TO UPGRADE                           │
├─────────────────────────────────────────────────────────────┤
│  Upgrade when:    │  • More than 500 users/day              │
│                   │  • Need 24/7 uptime                     │
│                   │  • Exceed 1,500 API calls/day           │
├─────────────────────────────────────────────────────────────┤
│  Paid Tier Cost   │  $5-20/month                            │
│  Supports         │  1,000-5,000 users/day                  │
└─────────────────────────────────────────────────────────────┘
```

---

## ⏱️ Time Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│  Step                     │  Time      │  Difficulty        │
├─────────────────────────────────────────────────────────────┤
│  1. Get API Key           │  5 min     │  ⭐ Easy           │
│  2. Deploy Backend        │  10 min    │  ⭐⭐ Medium       │
│  3. Configure Plugin      │  5 min     │  ⭐ Easy           │
│  4. Build & Test          │  7 min     │  ⭐ Easy           │
│  5. Publish               │  5 min     │  ⭐ Easy           │
├─────────────────────────────────────────────────────────────┤
│  TOTAL                    │  32 min    │  ⭐⭐ Medium       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 Documentation Map

```
START_HERE.md
    │
    ├─→ QUICK_START.md (30 min deployment)
    │   └─→ Follow this for fastest deployment
    │
    ├─→ DEPLOYMENT_GUIDE.md (detailed guide)
    │   └─→ All hosting options + troubleshooting
    │
    ├─→ DEPLOYMENT_CHECKLIST.md (track progress)
    │   └─→ Phase-by-phase checklist
    │
    ├─→ DEPLOYMENT_SUMMARY.md (overview)
    │   └─→ Quick reference
    │
    └─→ ARCHITECTURE.md (system design)
        └─→ Technical deep dive
```

---

## 🎓 Learning Path

```
Beginner Path:
1. Read START_HERE.md
2. Follow QUICK_START.md
3. Deploy to Railway
4. Test and publish

Intermediate Path:
1. Read DEPLOYMENT_GUIDE.md
2. Compare hosting options
3. Set up monitoring
4. Customize deployment

Advanced Path:
1. Read ARCHITECTURE.md
2. Understand system design
3. Optimize performance
4. Scale infrastructure
```

---

## ✅ Success Checklist

```
Pre-Deployment:
□ GitHub account created
□ Google account ready
□ Railway/Render account created
□ Figma Desktop installed
□ Repository cloned

Deployment:
□ Gemini API key obtained
□ Backend deployed
□ Redis connected
□ Celery worker running
□ Environment variables set

Plugin:
□ Backend URL updated
□ Network access configured
□ Plugin built successfully
□ Tested in Figma
□ No console errors

Publishing:
□ Plugin icon created
□ Screenshots taken
□ Description written
□ Submitted to Figma
□ Approved and live

Post-Deployment:
□ Monitoring set up
□ Shared with users
□ Feedback collected
□ Documentation updated
```

---

## 🚀 Ready to Deploy?

### Choose Your Guide:

**🏃 Fast Track (30 min)**
→ [QUICK_START.md](../QUICK_START.md)

**📚 Detailed Guide (1-2 hours)**
→ [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)

**✅ Track Progress**
→ [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)

---

**Good luck! 🎉**
