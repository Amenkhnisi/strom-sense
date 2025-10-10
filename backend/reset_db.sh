#!/bin/bash


  echo "Watching for model changes..."
  echo "Model change detected. Resetting DB..."
  echo "Dropping all tables..."
  docker exec -it EnergyDb psql -U postgres -d energy_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  echo "Recreating tables with Alembic..."
  docker exec -it ocr-backend alembic upgrade head
  echo "Display tables"
  docker exec -it EnergyDb psql -U postgres -d energy_db -c "\d users"
