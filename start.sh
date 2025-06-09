#!/bin/bash

# Family Tree Explorer - Production Startup Script for Render

echo "🚀 Starting Family Tree Explorer..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Start the application with Gunicorn
echo "🌟 Starting application with Gunicorn..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 app:app 