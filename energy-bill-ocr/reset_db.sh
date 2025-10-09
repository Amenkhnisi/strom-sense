#!/bin/bash


echo "Watching for model changes..."

while true; do
  inotifywait -e modify,create,delete -r ./models.py
  echo "Model change detected. Resetting DB..."
  echo "Dropping all tables..."
  docker exec -it EnergyDb psql -U postgres -d energy_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
  echo "Recreating tables with Alembic..."
  docker exec -it energy-bill-ocr alembic upgrade head
  echo "Display tables"
  docker exec -it EnergyDb psql -U postgres -d energy_db -c "\d users"
done