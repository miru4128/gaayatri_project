# 🚀 Quick Deployment Checklist for Render

Follow these steps to deploy your Gaayatri Project to Render.com.

## Prerequisites Checklist

- [ ] GitHub account with this repository pushed
- [ ] Render.com account (sign up at https://dashboard.render.com)
- [ ] Groq API key (get one at https://console.groq.com)

## Deployment Steps

### 1. Connect to Render
- [ ] Log in to Render Dashboard: https://dashboard.render.com
- [ ] Click **"New +"** button (top right)
- [ ] Select **"Blueprint"**
- [ ] Click **"Connect a repository"**
- [ ] If not connected, authorize GitHub access
- [ ] Find and select **miru4128/gaayatri_project**
- [ ] Click **"Connect"**

### 2. Review Blueprint Configuration
- [ ] Render will show the services from `render.yaml`:
  - **gaayatri-db**: PostgreSQL database (free)
  - **gaayatri-app**: Web service (free)
- [ ] Click **"Apply"** or **"Create"** to proceed

### 3. Configure Environment Variables
- [ ] Wait for the services to be created (~30 seconds)
- [ ] Click on **"gaayatri-app"** web service
- [ ] Go to **"Environment"** tab on the left
- [ ] Click **"Add Environment Variable"**
- [ ] Add the following:

```
Key: CHATBOT_API_KEY
Value: <paste your Groq API key here>
```

- [ ] Click **"Save Changes"**

### 4. Wait for Build
- [ ] Go to **"Logs"** tab
- [ ] Watch the build process:
  - [ ] Installing dependencies (may take 5-10 minutes)
  - [ ] Running migrations
  - [ ] Collecting static files
  - [ ] Starting Gunicorn
- [ ] Wait for: **"Your service is live 🎉"**

### 5. Create Admin User
- [ ] In the service page, go to **"Shell"** tab
- [ ] Click **"Connect"** or **"Launch Shell"**
- [ ] Run this command:
```bash
python manage.py createsuperuser
```
- [ ] Follow prompts to create username, email, password
- [ ] Exit shell when done

### 6. Verify Deployment
- [ ] Click on the service URL (top of page): `https://gaayatri-app.onrender.com`
- [ ] Verify the homepage loads
- [ ] Visit admin: `https://gaayatri-app.onrender.com/admin/`
- [ ] Log in with your superuser credentials
- [ ] Test basic functionality:
  - [ ] Create a test farmer user
  - [ ] Create a test doctor user
  - [ ] Try the chatbot
  - [ ] Test messaging

## Common Issues & Solutions

### Build Fails
**Issue**: Build times out or fails
- **Solution**: Check the logs for specific error messages
- **Solution**: Verify all environment variables are set
- **Solution**: Check that `render.yaml` is properly formatted

### Can't Access App
**Issue**: 404 or service unavailable
- **Solution**: Wait a few minutes, free tier has cold starts
- **Solution**: Check that service status is "Live" (not "Suspended")
- **Solution**: Verify the URL in your browser

### Chatbot Doesn't Work
**Issue**: Chatbot returns errors
- **Solution**: Verify `CHATBOT_API_KEY` is set correctly
- **Solution**: Check your Groq API key is valid at https://console.groq.com
- **Solution**: Check the service logs for specific error messages

### Database Connection Errors
**Issue**: App crashes with database errors
- **Solution**: Verify database is running (check gaayatri-db status)
- **Solution**: Check that `DATABASE_URL` environment variable is set (should be automatic)
- **Solution**: Try restarting the web service

## Post-Deployment Tasks

- [ ] Set up custom domain (optional, in Settings > Custom Domain)
- [ ] Enable auto-deploy on git push (should be on by default)
- [ ] Set up monitoring/alerts (optional, in Settings)
- [ ] Review and adjust environment variables as needed
- [ ] Backup database regularly (free tier includes 7-day backups)

## Your App URLs

After deployment, save these URLs:

- **App URL**: `https://gaayatri-app.onrender.com` (or your custom domain)
- **Admin Panel**: `https://gaayatri-app.onrender.com/admin/`
- **API Endpoint**: `https://gaayatri-app.onrender.com/chatbot/`

## Need Help?

- 📖 Full guide: See [DEPLOYMENT.md](DEPLOYMENT.md)
- 📚 Render docs: https://render.com/docs
- 💬 Render community: https://community.render.com
- 🐛 Issues: Open issue on GitHub

## Success! 🎉

If you see your app running at the Render URL, congratulations! Your Django app is now deployed.

Remember:
- Free tier apps sleep after 15 minutes of inactivity (cold start on next request)
- Database has 256 MB limit on free tier
- Consider upgrading to Starter plan ($7/month) for production use

---

**Note**: Keep your `CHATBOT_API_KEY` secret. Never commit it to Git or share it publicly.
