#!/bin/bash
# Build script for Render deployment
# This script simulates what Render will do during deployment

set -e  # Exit on error

echo "🚀 Starting build process..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run Django checks
echo "✅ Running Django system checks..."
python manage.py check --deploy

echo "✨ Build completed successfully!"
echo ""
echo "To start the server locally, run:"
echo "  gunicorn gaayatri_project.wsgi:application"
echo ""
echo "Or for development:"
echo "  python manage.py runserver"
