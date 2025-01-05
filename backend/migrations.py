from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from config.config import config

# Dynamically fetch the database URL
DATABASE_URL = config.get_database_url()


def check_migrations_and_apply():
    # Load Alembic configuration
    alembic_cfg = Config("alembic.ini")

    # Dynamically set the database URL
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

    # Optional: Add other configurations, if needed
    # alembic_cfg.set_main_option("some_key", "some_value")

    # Optional: Check if database exists
    engine = create_engine(DATABASE_URL)
    inspector = reflection.Inspector.from_engine(engine)

    # Run Alembic upgrade to head to apply any unapplied migrations
    print("Applying pending migrations (if any)...")
    command.upgrade(alembic_cfg, "head")


if __name__ == "__main__":
    check_migrations_and_apply()
