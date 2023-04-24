#! /usr/bin/env bash

# Let the DB start
python initials/db_starter.py

# Run migration
alembic upgrade heads

# add any inital data

python initials/initial_data.py

# run tests
# python -m pytest app/tests




# start application
sanic app.main:app --debug --reload