# ❓ Frequently Asked Questions (FAQ)

## General Questions

### What is Prompt2Figma?
Prompt2Figma is an AI-powered Figma plugin that converts natural language descriptions into UI wireframes. Simply describe what you want to design, and the plugin generates it on your Figma canvas.

### Is it really free?
Yes! Using free tiers:
- Railway/Render: Free hosting ($5 credit or 750 hours/month)
- Google Gemini: Free API (1,500 requests/day)
- Figma Plugin: Free to publish and use

**Total: $0/month** for personal use or small teams (100-500 users/day)

### How long does deployment take?
- **Quick deployment**: 30 minutes (following QUICK_START.md)
- **Detailed deployment**: 1-2 hours (following DEPLOYMENT_GUIDE.md)
- **Local testing**: 20 minutes

### Do I need coding experience?
Basic familiarity with command line is helpful, but not required. The guides are written for beginners with step-by-step instructions.

---

## Deployment Questions

### Which hosting platform should I choose?

**Railway.app (Recommended)**
- ✅ Easiest to set up
- ✅ Built-in Redis
- ✅ $5 free credit/month
- ✅ Auto-deploy from GitHub
- ❌ Limited free tier

**Render.com**
- ✅ 750 hours/month free
- ✅ Good documentation
- ✅ Auto-deploy from GitHub
- ❌ Sleeps after 15 min inactivity

**Fly.io**
- ✅ Most flexible
- ✅ Generous free tier
- ✅ Global deployment
- ❌ Requires Docker knowledge

**Recommendation**: Start with Railway for easiest setup.

### Can I deploy without a credit card?
Yes! Railway and Render offer free tiers without requiring a credit card initially. However, you may need to add one to verify your account or access certain features.

### What if I exceed the free tier limits?
You'll receive notifications before hitting limits. Options:
1. Upgrade to paid tier ($5-20/month)
2. Optimize usage (caching, rate limiting)
3. Switch to a different platform
4. Implement usage quotas

### Can I use my own domain?
Yes! Most hosting platforms allow custom domains:
- Railway: Add custom domain in settings
- Render: Configure custom domain
- Fly.io: Use `fly certs` command

Custom domains are optional and not required for the plugin to work.

---

## API Questions

### How do I get a Google Gemini API key?
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)
5. Keep it secure - never commit to Git

### What are the Gemini API rate limits?
**Free Tier:**
- 60 requests per minute
- 1,500 requests per day
- Sufficient for 100-500 users/day

**Paid Tier:**
- Higher limits available
- Pay-as-you-go pricing
- See https://ai.google.dev/pricing

### Can I use a different AI provider?
Yes! The backend supports:
- Google Gemini (default, recommended)
- Ollama (self-hosted, free but requires setup)
- OpenAI (requires API key and payment)

To switch providers, modify `app/core/services/orchestrator.py`.

### What happens if I hit the API rate limit?
The backend implements automatic retry logic with exponential backoff. Users will see a temporary error message asking them to try again in a few seconds.

---

## Plugin Questions

### How do I update the plugin after deployment?
1. Make changes to plugin code
2. Rebuild: `npm run build`
3. In Figma: Plugins → Development → Reload plugin
4. Test changes
5. Republish if needed

### Can users install my plugin before it's approved?
Yes! You can share the plugin privately:
1. Publish as "Organization only"
2. Share the plugin link
3. Users can install without Figma review

Public plugins require Figma team approval (1-2 weeks).

### How do I update the backend URL after deployment?
1. **Automatic**: Run `node configure-plugin.js`
2. **Manual**: Edit `src/ui/ui.js` line 830
3. Rebuild plugin: `npm run build`
4. Reload in Figma

### What if my backend URL changes?
Update the plugin configuration and rebuild:
```bash
node configure-plugin.js  # Enter new URL
cd "prompt2Figma-Frontend (Plugin)"
npm run build
```

Then reload the plugin in Figma.

---

## Technical Questions

### What technologies are used?

**Backend:**
- Python 3.9+ (FastAPI)
- Celery (task queue)
- Redis (database)
- Google Gemini (AI)

**Frontend:**
- TypeScript
- Figma Plugin API
- esbuild (bundler)

**Deployment:**
- Railway/Render/Fly.io
- Docker (optional)
- GitHub (version control)

### Do I need Redis?
Yes, Redis is required for:
- Celery message broker
- Task result storage
- Application state management
- Session caching

All hosting platforms provide free Redis instances.

### Can I run this locally?
Yes! For local development:
1. Install Redis: `redis-server`
2. Start backend: `uvicorn app.main:app --reload`
3. Start worker: `celery -A app.tasks.celery_app worker`
4. Build plugin: `npm run build`
5. Load in Figma Desktop

See README.md for detailed local setup.

### How do I debug issues?

**Backend Issues:**
- Check deployment logs (Railway/Render dashboard)
- Visit `/health` endpoint
- Check `/docs` for API documentation
- Review environment variables

**Plugin Issues:**
- Open Figma DevTools (Plugins → Development → Open Console)
- Check browser console for errors
- Verify backend URL is correct
- Test with simple prompts first

**API Issues:**
- Check Google Cloud Console
- Verify API key is correct
- Check quota usage
- Review rate limits

---

## Security Questions

### Is my API key secure?
Yes, if you follow best practices:
- ✅ Store in environment variables only
- ✅ Never commit to Git (use .gitignore)
- ✅ Use platform secrets management
- ❌ Never hardcode in source code
- ❌ Never share publicly

### How do I protect against abuse?
The backend includes:
- Rate limiting (per-minute, per-hour, per-day)
- Input sanitization (XSS, SQL injection prevention)
- Request validation (Pydantic schemas)
- CORS configuration
- Session security

Additional protection:
- Monitor usage regularly
- Set up alerts for unusual activity
- Implement user authentication (optional)
- Add API key rotation

### Can users see my API key?
No. The API key is stored on your backend server, not in the plugin. Users never have access to it.

### Should I enable CORS for all origins?
For development: Yes (allow all origins)
For production: No (restrict to Figma domains)

Update `app/main.py`:
```python
allow_origins=[
    "https://www.figma.com",
    "https://figma.com"
]
```

---

## Usage Questions

### What kind of prompts work best?
**Good prompts:**
- "Create a login form with email and password"
- "Design a mobile dashboard with stats cards"
- "Make a dark mode settings page"

**Better prompts:**
- "Create a mobile login form with email input, password input, forgot password link, and blue submit button"
- "Design a desktop analytics dashboard with sidebar navigation, top bar with user profile, and main content area with 3 chart cards"

**Tips:**
- Be specific about layout (mobile/desktop)
- Mention key components
- Specify colors/themes if desired
- Include interaction elements

### Can I edit generated wireframes?
Yes! The plugin supports iterative editing:
1. Generate initial wireframe
2. Enter edit prompt: "Add a forgot password link"
3. Click "Apply Edit"
4. Wireframe updates with context awareness

### Can I generate code from wireframes?
Yes! Click "Generate Code" to get:
- React component code
- Validated syntax (AST validation)
- Ready to use in your project

### How accurate are the generated wireframes?
Accuracy depends on:
- Prompt clarity (specific prompts = better results)
- AI model capabilities (Gemini is quite good)
- Component complexity (simpler = more accurate)

Typical accuracy: 80-90% for common UI patterns.

---

## Scaling Questions

### When should I upgrade from free tier?
Upgrade when you have:
- More than 500 active users/day
- Need 24/7 uptime (no cold starts)
- Exceed 1,500 Gemini API calls/day
- Want faster response times

### How much does scaling cost?
**Small scale** ($5-10/month):
- 1,000-5,000 users/day
- Always-on backend
- 2 Celery workers

**Medium scale** ($20-50/month):
- 10,000-50,000 users/day
- Load balanced backend
- 5-10 Celery workers
- Larger Redis instance

**Large scale** ($100+/month):
- 100,000+ users/day
- Auto-scaling infrastructure
- Redis cluster
- CDN integration

### Can I handle 1000 users on free tier?
Not simultaneously. Free tier supports:
- 100-500 users/day (spread throughout the day)
- 10-50 concurrent users
- 1,500 AI requests/day

For 1000+ users/day, upgrade to paid tier.

### How do I optimize costs?
1. **Implement caching**: Cache common prompts
2. **Rate limiting**: Prevent abuse
3. **Optimize workers**: Use single worker initially
4. **Monitor usage**: Track and optimize API calls
5. **Use CDN**: Serve static assets efficiently

---

## Troubleshooting Questions

### Plugin can't connect to backend
**Check:**
1. Backend URL in `ui.js` is correct
2. Backend is running (visit URL in browser)
3. URL uses HTTPS (not HTTP)
4. Network access configured in `manifest.json`
5. CORS settings allow Figma domains

**Test:**
```bash
curl https://your-app.railway.app/health
# Should return: {"status":"healthy",...}
```

### Gemini API returns errors
**Common causes:**
1. Invalid API key
2. Rate limit exceeded (60/min or 1500/day)
3. API key not enabled for Gemini
4. Network connectivity issues

**Solutions:**
1. Verify API key in environment variables
2. Wait and retry if rate limited
3. Check Google Cloud Console
4. Test API key with curl

### Backend deployment fails
**Common causes:**
1. Missing environment variables
2. Redis not connected
3. Python version mismatch
4. Dependency installation errors

**Solutions:**
1. Check deployment logs
2. Verify all env variables are set
3. Ensure Python 3.9+ is used
4. Review requirements.txt

### Plugin doesn't render wireframes
**Common causes:**
1. Invalid JSON from backend
2. JavaScript errors in plugin
3. Figma API issues
4. Network timeout

**Solutions:**
1. Check Figma DevTools console
2. Test with simple prompt
3. Verify backend returns valid JSON
4. Rebuild plugin: `npm run build`

---

## Publishing Questions

### How long does Figma review take?
Typically 1-2 weeks for public plugins. Private/organization plugins don't require review.

### What if my plugin is rejected?
Figma will provide feedback. Common reasons:
- Incomplete description
- Missing screenshots
- Broken functionality
- Security concerns

Fix issues and resubmit.

### Can I update my plugin after publishing?
Yes! Update process:
1. Make changes to code
2. Rebuild plugin
3. Test thoroughly
4. Republish (same process)
5. Users get automatic updates

### How do I promote my plugin?
1. **Figma Community**: Optimize description and tags
2. **Social Media**: Share on Twitter, LinkedIn
3. **Design Communities**: Post on Reddit, Designer News
4. **Content**: Create tutorial videos, blog posts
5. **SEO**: Use relevant keywords in description

---

## Maintenance Questions

### How often should I update dependencies?
**Recommended schedule:**
- Security updates: Immediately
- Minor updates: Monthly
- Major updates: Quarterly

**Commands:**
```bash
# Backend
pip list --outdated
pip install -U package_name

# Plugin
npm outdated
npm update
```

### How do I monitor uptime?
Use free monitoring tools:
1. **UptimeRobot**: https://uptimerobot.com
   - Monitor `/health` endpoint
   - Email alerts on downtime
   - Free: 50 monitors

2. **Better Stack**: https://betterstack.com
   - Log aggregation
   - Error tracking
   - Free tier available

3. **Sentry**: https://sentry.io
   - Error tracking
   - Performance monitoring
   - Free: 5K events/month

### What logs should I monitor?
**Critical logs:**
- Backend errors (500 errors)
- API failures (Gemini errors)
- Rate limit hits
- Deployment failures

**Useful logs:**
- Request patterns
- Response times
- User behavior
- Resource usage

### How do I backup data?
**Redis data:**
```bash
# Railway/Render provide automatic backups
# Manual backup:
redis-cli --rdb /path/to/backup.rdb
```

**Code:**
- Use Git for version control
- Push to GitHub regularly
- Tag releases

---

## Support Questions

### Where can I get help?
1. **Documentation**: Check guides first
2. **Logs**: Review deployment and plugin logs
3. **Community**: Figma forums, Reddit
4. **GitHub**: Open an issue
5. **Platform Support**: Railway/Render support

### How do I report bugs?
1. Check if issue already exists
2. Gather information:
   - Error messages
   - Steps to reproduce
   - Environment details
   - Logs
3. Open GitHub issue with details

### Can I contribute to the project?
Yes! Contributions welcome:
1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

See CONTRIBUTING.md for guidelines.

### Is there a community?
Currently:
- GitHub Discussions
- Figma Community comments
- Twitter hashtag: #Prompt2Figma

Consider creating:
- Discord server
- Slack workspace
- Reddit community

---

## Advanced Questions

### Can I customize the AI prompts?
Yes! Modify `app/core/services/orchestrator.py`:
- Adjust system prompts
- Add custom instructions
- Fine-tune output format

### Can I add authentication?
Yes! Add authentication layer:
1. Implement user accounts
2. Add API key per user
3. Track usage per user
4. Implement quotas

Requires additional database (PostgreSQL).

### Can I white-label the plugin?
Yes! You can:
- Change plugin name
- Update branding
- Modify UI design
- Add custom features

Ensure compliance with licenses.

### Can I monetize the plugin?
Yes! Options:
1. **Freemium**: Free basic, paid premium
2. **Subscription**: Monthly/yearly plans
3. **Usage-based**: Pay per generation
4. **Enterprise**: Custom pricing

Requires payment integration and user management.

---

## Still Have Questions?

### Check Documentation
- [START_HERE.md](START_HERE.md) - Overview
- [QUICK_START.md](QUICK_START.md) - Fast deployment
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Detailed guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details

### Get Support
- Open GitHub issue
- Check platform documentation
- Ask in Figma community

---

**Can't find your question? Open an issue on GitHub!** 🚀
