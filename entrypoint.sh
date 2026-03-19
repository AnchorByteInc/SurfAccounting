#!/bin/sh
set -e

# Initialize/Migrate database
echo "Initializing/Migrating database..."
# Run reset_db.py if database doesn't exist, or just use migrations
if [ ! -f "data.sqlite" ]; then
    python3 scripts/reset_db.py --force
fi

# Apply migrations
flask db upgrade

# Start Nginx in background
echo "Starting Nginx..."
nginx -g "daemon on;"

# Start Backend via Gunicorn
echo "Starting Backend with Gunicorn..."
exec gunicorn --bind 127.0.0.1:5001 "backend.app:create_app()"
