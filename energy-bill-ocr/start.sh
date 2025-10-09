#!/bin/bash

echo "Checking if Alembic migration is needed..."

# Run only if the database is empty or missing the 'users' table
if alembic current | grep -q "None"; then
  echo "Running Alembic migrations..."
  alembic upgrade head
else
  echo "Alembic already applied. Skipping migration."
fi

echo "Starting FastAPI app..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

