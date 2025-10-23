import os
import shutil
import subprocess
from sqlalchemy import create_engine
from database import Base, engine  # your declarative base

ALEMBIC_VERSIONS_DIR = os.path.join("alembic", "versions")


def clear_migrations():
    if os.path.exists(ALEMBIC_VERSIONS_DIR):
        for filename in os.listdir(ALEMBIC_VERSIONS_DIR):
            file_path = os.path.join(ALEMBIC_VERSIONS_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("✅ Alembic versions cleared.")
    else:
        print("⚠️ Alembic versions directory not found.")


def reset_database():
    print("🧨 Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("🛠️ Recreating all tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset complete.")


def stamp_head():
    print("📌 Stamping current DB state as Alembic head...")
    subprocess.run(["alembic", "stamp", "head"], check=True)
    print("✅ Alembic stamped.")


def generate_initial_migration():
    print("🆕 Generating new initial migration...")
    subprocess.run(["alembic", "revision", "--autogenerate",
                   "-m", "initial"], check=True)
    print("✅ Initial migration created.")


def upgrade_head():
    print("🚀 Applying migration...")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("✅ Database upgraded to head.")


if __name__ == "__main__":
    clear_migrations()
    reset_database()
    stamp_head()
    generate_initial_migration()
    upgrade_head()
