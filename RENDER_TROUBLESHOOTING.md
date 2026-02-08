# Render Deployment Troubleshooting Guide

## Common Deployment Failures and Solutions

### Issue: Deploy Failed - Build Timeout

**Symptom**: Deployment fails with "Create web service gaayatri-app-xxxx (deploy failed)"

**Root Cause**: The application includes large machine learning dependencies:
- `torch` (~800MB download)
- `sentence-transformers` (~200MB + model downloads)

On Render's free tier (512MB RAM), these can cause:
1. Build timeouts (exceeds default build time)
2. Memory exhaustion during pip install
3. Slow cold starts after service sleep

### Solutions (Choose One)

#### Solution 1: Wait for Full Build (Recommended for Production)
The full build with ML dependencies takes **5-10 minutes** on free tier. Be patient and let it complete.

**What's happening:**
```bash
# Your build is doing this:
pip install torch  # ~800MB, takes 3-5 minutes
pip install sentence-transformers  # ~200MB, takes 1-2 minutes
# Plus model download on first run: ~100MB
```

**To deploy with full features:**
1. Use the current `requirements.txt` (includes torch and sentence-transformers)
2. Deploy via Blueprint
3. **Wait 10-15 minutes** for first build
4. Don't cancel - Render may show "Building..." for a long time
5. Check logs to see progress

#### Solution 2: Use Minimal Requirements (Faster Deployment)
For **faster deployment without semantic filtering**, use minimal requirements:

1. **Before deploying**, rename files:
   ```bash
   mv requirements.txt requirements-full.txt
   mv requirements-minimal.txt requirements.txt
   ```

2. Deploy to Render (will complete in ~2-3 minutes)

3. The chatbot will work but without semantic similarity filtering

4. **To re-enable full features later:**
   ```bash
   mv requirements.txt requirements-minimal.txt
   mv requirements-full.txt requirements.txt
   git commit && git push  # Trigger redeploy
   ```

#### Solution 3: Upgrade to Render Starter Plan
**Cost**: $7/month per service
**Benefits**:
- More RAM (512MB → 2GB+)
- Faster builds
- No cold starts
- Better performance

This is recommended for production use.

### Specific Error Messages and Fixes

#### "Build command failed"
- **Check logs** for specific error (Render Dashboard → Logs)
- Common causes:
  - Pip install timeout → Wait longer or use minimal requirements
  - Memory exhaustion → Upgrade plan or use minimal requirements
  - Missing dependencies → Check requirements.txt syntax

#### "Service failed to start"
- **Possible causes:**
  - Missing `CHATBOT_API_KEY` environment variable (required!)
  - Database not ready → Wait 30 seconds and retry
  - Port binding issue → Check gunicorn command in render.yaml

**Fix:**
1. Go to Render Dashboard → Environment
2. Add: `CHATBOT_API_KEY` = your Groq API key
3. Save changes (triggers redeploy)

#### "Database connection failed"
- Database service may not be ready yet
- **Solution:** Wait 1-2 minutes after database creation before deploying web service

### Optimization Tips

#### 1. Reduce Build Time
Edit `render.yaml` build command:
```yaml
buildCommand: |
  pip install --upgrade pip
  pip install --no-cache-dir -r requirements.txt  # Use less memory
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
```

#### 2. Add Build Status Checks
In your build command:
```yaml
buildCommand: |
  echo "Installing dependencies..."
  pip install -r requirements.txt
  echo "Running migrations..."
  python manage.py migrate --noinput
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
  echo "Build complete!"
```

#### 3. Increase Gunicorn Timeout
For slow ML model loading:
```yaml
startCommand: gunicorn gaayatri_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### Verification Steps

After successful deployment:

1. **Check service status**: Should show "Live" in Render dashboard
2. **Check logs**: Look for "Booting worker" messages
3. **Access app**: Open the Render URL (https://gaayatri-app.onrender.com)
4. **Test admin**: Go to /admin/ and log in
5. **Test chatbot**: Try asking a cattle-related question

### When to Use Each Requirements File

| File | Use Case | Build Time | Features |
|------|----------|------------|----------|
| `requirements.txt` | Production | 5-10 min | Full features + semantic filtering |
| `requirements-minimal.txt` | Quick test/demo | 2-3 min | All features except semantic filtering |

### Still Having Issues?

1. **Check the logs**: Render Dashboard → Your Service → Logs tab
2. **Look for specific errors**: Python tracebacks, pip errors, etc.
3. **Common patterns**:
   - "Killed" → Memory exhaustion (upgrade plan)
   - "Timeout" → Build too slow (use minimal requirements or upgrade)
   - "ModuleNotFoundError" → Check requirements.txt
   - "Connection refused" → Database not ready (wait and retry)

### Environment Variables Checklist

Ensure these are set in Render Dashboard → Environment:

✅ **Auto-configured** (by render.yaml):
- `PYTHON_VERSION` = 3.12
- `DJANGO_SETTINGS_MODULE` = gaayatri_project.settings
- `DJANGO_SECRET_KEY` = (auto-generated)
- `DEBUG` = False
- `DATABASE_URL` = (from database service)

⚠️ **You must add**:
- `CHATBOT_API_KEY` = your Groq API key

### Performance Expectations

**Free Tier**:
- Build time: 5-10 minutes (first time), 3-5 minutes (subsequent)
- Cold start: 30-60 seconds after 15 min inactivity
- Response time: 200-500ms (warm), 30-60s (cold start)
- Model loading: First chatbot request may take 10-15 seconds

**Starter Plan** ($7/month):
- Build time: 3-5 minutes
- No cold starts
- Response time: 100-200ms consistently
- Model loading: 2-3 seconds first request

### Alternative Deployment Strategy

If Render continues to fail, consider:

1. **Deploy without ML features first** (use requirements-minimal.txt)
2. **Verify everything works**
3. **Then add ML features** by switching to full requirements.txt
4. This validates your config before tackling the large dependencies

### Summary

The deployment failure is most likely due to:
1. **Large torch/ML dependencies** taking too long to build
2. **Insufficient patience** - builds can take 10+ minutes
3. **Memory constraints** on free tier

**Quick Fix**: Use `requirements-minimal.txt` for instant deployment, add ML later.

**Best Fix**: Be patient, let the full build complete (10-15 minutes first time).

---

**Need more help?** Check:
- Main deployment guide: `DEPLOYMENT.md`
- Architecture details: `ARCHITECTURE.md`
- Render documentation: https://render.com/docs
