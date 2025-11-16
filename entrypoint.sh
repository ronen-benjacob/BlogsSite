#!/bin/bash
# Entrypoint script for Flask application
# Initializes database before starting the app

echo "Starting Flask Blog Application..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0

until python -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(os.environ.get('SQLALCHEMY_DATABASE_URI').replace('postgresql://', 'postgresql://').split('?')[0])
    conn.close()
    print('PostgreSQL is ready!')
    sys.exit(0)
except Exception as e:
    print(f'PostgreSQL not ready: {e}')
    sys.exit(1)
" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo "PostgreSQL did not become ready in time"
        exit 1
    fi
    echo "Waiting for PostgreSQL... ($attempt/$max_attempts)"
    sleep 2
done

# Initialize database tables
echo "Initializing database tables..."
python init_db.py

if [ $? -ne 0 ]; then
    echo "Database initialization failed"
    exit 1
fi

echo "✅ Database initialization complete"

# Start the application
echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:5003 --workers 2 --timeout 120 main:app