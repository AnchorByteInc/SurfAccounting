#!/bin/sh
set -e

# Initialize/Migrate database
echo "Initializing/Migrating database..."
# Apply migrations
flask db upgrade

# Seed default data if needed (safe, only seeds if empty)
python3 scripts/seed_db.py

# Start Nginx in background
echo "Starting Nginx..."
nginx -g "daemon on;"

# Start Backend via Gunicorn
echo "Starting Backend with Gunicorn..."
exec gunicorn --bind 127.0.0.1:5001 "backend.app:create_app()"
