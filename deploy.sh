#! /usr/bin/env bash
# pip install --upgrade pip



export PYTHONPATH=$PWD

# #install dependencies
# pip install -r requirements.txt

# # Initialize database
# python initials/db_starter.py

# Run migrations
alembic upgrade heads

# Create initial data
python initials/initial_data.py
if [ -f .env ]; then
    source .env
fi
