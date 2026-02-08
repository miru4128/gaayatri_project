# Gaayatri Project

A Django-based web application for farmers and veterinary doctors to manage cattle, inventory, finances, and communicate through an AI-powered chatbot.

## 🚀 Quick Deploy to Render

**Ready to deploy?** See the [DEPLOYMENT.md](DEPLOYMENT.md) guide for step-by-step instructions.

⚠️ **Having deployment issues?** Check [RENDER_TROUBLESHOOTING.md](RENDER_TROUBLESHOOTING.md)

The repository is pre-configured with `render.yaml` for one-click deployment to Render.com.

**Two deployment options:**
- **Fast** (2-3 min): Use `requirements-minimal.txt` - all features except ML
- **Full** (10-15 min): Use `requirements.txt` - includes ML-powered semantic filtering

## Features

- **User Management**: Separate dashboards for farmers and doctors
- **Cattle Management**: Track cattle information, health, and milk yield
- **Inventory Management**: Monitor feed and supplies with automatic alerts
- **Financial Tracking**: Record income and expenses
- **Messaging System**: Direct communication between farmers and doctors
- **AI Chatbot**: Get answers to farming and veterinary questions using AI

## Requirements

- Python 3.12+
- PostgreSQL (for production) or SQLite (for development)
- See `requirements.txt` for Python dependencies

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/miru4128/gaayatri_project.git
cd gaayatri_project
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file (optional for local development):
```bash
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
CHATBOT_API_KEY=your-groq-api-key-here
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Access the application at `http://localhost:8000`

## Deployment

### 🚀 Deploy to Render.com

**For complete deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

Quick summary:

1. Push your code to GitHub
2. Connect to Render using Blueprint (detects `render.yaml` automatically)
3. Add required environment variable: `CHATBOT_API_KEY` (your Groq API key)
4. Wait for build and deployment (~5-10 minutes first time)
5. Create superuser via Render Shell
6. Access your live app!

This project includes:
- ✅ `render.yaml` - Automated deployment configuration
- ✅ `runtime.txt` - Python version specification
- ✅ `build.sh` - Local build testing script
- ✅ `.env.example` - Environment variables template

### Environment Variables

- `DEBUG`: Set to `False` in production
- `DJANGO_SECRET_KEY`: Secret key for Django (keep this secure!)
- `DATABASE_URL`: Database connection string (automatically set in production)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames
- `CHATBOT_API_KEY` or `GROQ_API_KEY`: API key for the chatbot service
- `CHATBOT_MODEL`: Model to use for chatbot (optional)
- `CHATBOT_EMBED_MODEL`: Embedding model for similarity search (default: all-MiniLM-L6-v2)

## Project Structure

```
gaayatri_project/
├── core/                   # Main app (users, cattle, inventory, messaging)
├── chatbot/                # AI chatbot functionality
├── gaayatri_project/       # Project settings
├── media/                  # User-uploaded files
├── staticfiles/            # Collected static files (generated)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── Procfile              # Process file for deployment
└── render.yaml           # Render.com configuration
```

## Key Technologies

- **Backend**: Django 6.0.2
- **Database**: PostgreSQL (production) / SQLite (development)
- **AI**: Groq API for chatbot, Sentence Transformers for embeddings
- **Deployment**: Gunicorn, WhiteNoise for static files
- **Styling**: Bootstrap (included in templates)

## License

This project is for educational/personal use.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
