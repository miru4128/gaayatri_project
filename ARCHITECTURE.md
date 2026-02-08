# 🏗️ Gaayatri Project - Render Architecture

## Deployment Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         GitHub Repository                    │
│                    miru4128/gaayatri_project                 │
│                                                              │
│  Files used by Render:                                      │
│  • render.yaml         (service configuration)              │
│  • requirements.txt    (Python dependencies)                │
│  • runtime.txt         (Python version)                     │
│  • manage.py          (Django management)                   │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ Auto-deploy on push
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                      Render.com Platform                     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Blueprint Deployment (render.yaml)         │    │
│  │                                                     │    │
│  │  Creates two services automatically:               │    │
│  │  1. PostgreSQL Database                            │    │
│  │  2. Web Service (Django App)                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  ┃              PostgreSQL Database                   ┃    │
│  ┃              Name: gaayatri-db                     ┃    │
│  ┃              Plan: Free (256 MB)                   ┃    │
│  ┃              Region: Auto-selected                 ┃    │
│  ┃                                                     ┃    │
│  ┃  • Automatic daily backups (7-day retention)      ┃    │
│  ┃  • Provides DATABASE_URL to web service           ┃    │
│  ┃  • SSL encrypted connections                      ┃    │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│                           │                                  │
│                           │ DATABASE_URL                     │
│                           │ (internal connection)            │
│                           ▼                                  │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓    │
│  ┃              Web Service                           ┃    │
│  ┃              Name: gaayatri-app                    ┃    │
│  ┃              Plan: Free (512 MB RAM)               ┃    │
│  ┃              Environment: Python 3.12              ┃    │
│  ┃                                                     ┃    │
│  ┃  Build Process (automated):                        ┃    │
│  ┃  1. pip install -r requirements.txt                ┃    │
│  ┃  2. python manage.py migrate                       ┃    │
│  ┃  3. python manage.py collectstatic --noinput       ┃    │
│  ┃                                                     ┃    │
│  ┃  Runtime:                                          ┃    │
│  ┃  • gunicorn gaayatri_project.wsgi:application     ┃    │
│  ┃  • Binds to 0.0.0.0:$PORT                         ┃    │
│  ┃  • Auto-restart on crashes                        ┃    │
│  ┃                                                     ┃    │
│  ┃  Static Files:                                     ┃    │
│  ┃  • Served by WhiteNoise middleware                ┃    │
│  ┃  • Compressed with Brotli                         ┃    │
│  ┃                                                     ┃    │
│  ┃  Environment Variables:                            ┃    │
│  ┃  • DJANGO_SECRET_KEY (auto-generated)             ┃    │
│  ┃  • DATABASE_URL (from database)                   ┃    │
│  ┃  • CHATBOT_API_KEY (user-provided) ⚠️            ┃    │
│  ┃  • DEBUG=False                                     ┃    │
│  ┃  • PYTHON_VERSION=3.12                            ┃    │
│  ┃  • RENDER_EXTERNAL_HOSTNAME (auto-set)           ┃    │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛    │
│                           │                                  │
│                           │ HTTPS (automatic SSL)            │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            │
                            ▼
                ┌───────────────────────┐
                │   Public Internet     │
                │                       │
                │  https://gaayatri-   │
                │  app.onrender.com    │
                └───────────────────────┘
                            │
                            │
                            ▼
                    ┌───────────────┐
                    │     Users     │
                    │  (Browsers)   │
                    └───────────────┘
```

## Component Details

### 1. GitHub Repository
- **Purpose**: Source code hosting and version control
- **Trigger**: Push to `main` branch triggers auto-deploy
- **Configuration Files**:
  - `render.yaml`: Blueprint configuration
  - `requirements.txt`: Python packages
  - `runtime.txt`: Python version (3.12.3)
  - `Procfile`: Alternative to render.yaml start command

### 2. PostgreSQL Database (gaayatri-db)
- **Type**: Managed PostgreSQL service
- **Plan**: Free tier
  - 256 MB storage
  - Automatic daily backups (7 days)
  - 97 GB outbound data transfer/month
- **Access**: Internal connection only (DATABASE_URL)
- **Data Stored**:
  - User accounts (farmers, doctors)
  - Cattle records
  - Inventory items
  - Financial records
  - Chat messages
  - Chatbot conversation history

### 3. Web Service (gaayatri-app)
- **Type**: Python web application
- **Plan**: Free tier
  - 512 MB RAM
  - Shared CPU
  - 100 GB outbound data transfer/month
  - Sleeps after 15 min inactivity
- **Tech Stack**:
  - Django 6.0.2
  - Gunicorn (WSGI server)
  - WhiteNoise (static files)
  - Channels (WebSocket support)
- **External APIs**:
  - Groq API (AI chatbot)
  - HuggingFace (optional, for embeddings)

### 4. Application Features

#### User Management
- Farmer accounts with farm profiles
- Doctor accounts with specializations
- Django admin panel

#### Core Features
- **Cattle Management**: Track health, milk yield, vaccinations
- **Inventory System**: Monitor feed, supplies, alerts
- **Financial Records**: Income/expense tracking
- **Messaging**: Direct farmer-doctor communication
- **AI Chatbot**: Groq-powered Q&A system
  - Context-aware responses
  - Semantic similarity matching
  - Conversation history

#### Security Features
- HTTPS enforced (Render automatic SSL)
- CSRF protection enabled
- Secure session cookies
- Database connection encryption
- Environment-based secrets

## Data Flow

### 1. User Request Flow
```
User Browser → HTTPS → Render Load Balancer → gunicorn → Django → PostgreSQL
                                                    ↓
                                              Static Files
                                              (WhiteNoise)
```

### 2. Chatbot Request Flow
```
User → Django View → Groq API → AI Response → Django → User
                ↓
         Conversation History
               (PostgreSQL)
```

### 3. Deployment Flow
```
Git Push → GitHub → Render Webhook → Build Process → Deploy → Live App
                                           ↓
                                    Run Tests (optional)
                                    Migrate Database
                                    Collect Static Files
```

## Environment Variables Reference

| Variable | Source | Required | Purpose |
|----------|--------|----------|---------|
| `DATABASE_URL` | Render (auto) | ✅ Yes | PostgreSQL connection |
| `DJANGO_SECRET_KEY` | Render (auto) | ✅ Yes | Django security |
| `CHATBOT_API_KEY` | User | ✅ Yes | Groq AI access |
| `DEBUG` | render.yaml | ✅ Yes | Debug mode (False) |
| `PYTHON_VERSION` | render.yaml | ✅ Yes | Python 3.12 |
| `RENDER_EXTERNAL_HOSTNAME` | Render (auto) | ✅ Yes | App hostname |
| `ALLOWED_HOSTS` | Auto-configured | No | Django hosts |
| `CSRF_TRUSTED_ORIGINS` | Auto-configured | No | CSRF origins |
| `CHATBOT_MODEL` | User (optional) | No | AI model name |
| `CHATBOT_EMBED_MODEL` | User (optional) | No | Embedding model |

## Resource Limits (Free Tier)

### PostgreSQL Database
- ✅ 256 MB storage
- ✅ 97 GB data transfer/month
- ✅ Daily backups (7 days)
- ❌ Limited connections (20)

### Web Service
- ✅ 512 MB RAM
- ✅ 100 GB data transfer/month
- ✅ Automatic HTTPS
- ❌ Sleeps after 15 min inactivity
- ❌ Shared CPU (slower performance)

### Upgrade Path
For production use, consider:
- **Starter Plan** ($7/month):
  - No sleep/cold starts
  - Better performance
  - More RAM
- **Database Upgrade** ($7/month):
  - More storage
  - Better performance
  - More connections

## Monitoring & Maintenance

### Available Tools
1. **Logs**: Real-time application logs
2. **Metrics**: CPU, memory, request metrics
3. **Shell**: SSH access for management commands
4. **Events**: Deployment and error events
5. **Alerts**: Email notifications (paid plans)

### Maintenance Tasks
- ✅ Automatic backups (daily)
- ✅ Automatic SSL renewal
- ✅ Automatic security patches
- ⚠️ Manual database migrations (on deploy)
- ⚠️ Manual superuser creation (one-time)

## Security Considerations

### Implemented
- ✅ HTTPS enforced (automatic SSL)
- ✅ Secure cookies (session, CSRF)
- ✅ DEBUG=False in production
- ✅ Random SECRET_KEY
- ✅ Database encryption at rest
- ✅ Environment variable secrets
- ✅ Django security middleware

### User Responsibilities
- 🔒 Keep CHATBOT_API_KEY secret
- 🔒 Use strong admin passwords
- 🔒 Regularly update dependencies
- 🔒 Monitor access logs
- 🔒 Review and limit user permissions

## Cost Breakdown (Free Tier)

| Service | Plan | Cost | Limits |
|---------|------|------|--------|
| Web Service | Free | $0 | 750 hrs/month, 512 MB RAM |
| PostgreSQL | Free | $0 | 256 MB, 20 connections |
| SSL Certificate | Free | $0 | Automatic renewal |
| Data Transfer | Included | $0 | 100 GB/month web, 97 GB/month DB |
| **Total** | | **$0/month** | Good for development/testing |

### Estimated Production Costs
- Web Service Starter: $7/month
- Database Starter: $7/month
- **Total**: ~$14/month for production-ready setup

---

**Note**: This architecture provides a solid foundation for development and testing. For production use with higher traffic, consider upgrading to paid plans for better performance and reliability.
