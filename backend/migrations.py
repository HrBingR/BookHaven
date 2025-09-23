from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import reflection
from functions.db import get_database_url
from sqlalchemy.exc import SQLAlchemyError
from config.logger import logger
import sys

# Dynamically fetch the database URL
DATABASE_URL = get_database_url()


def check_migrations_and_apply():
    try:
        # Load Alembic configuration
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)

        # Create engine and inspector
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        logger.info("Starting migration process...")

        # Get current revision before upgrade
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(alembic_cfg)
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        # Get latest available revision
        head_rev = script.get_current_head()

        if current_rev == head_rev:
            logger.info("Database is up to date, no migrations needed")
            return True

        logger.info(f"Current revision: {current_rev}")
        logger.info(f"Target revision: {head_rev}")
        logger.info("Applying pending migrations...")

        # Run the upgrade
        command.upgrade(alembic_cfg, "head")

        # Verify the upgrade
        with engine.begin() as connection:
            context = MigrationContext.configure(connection)
            new_rev = context.get_current_revision()

        if new_rev == head_rev:
            logger.info("Migrations completed successfully")
            logger.info(f"New revision: {new_rev}")
            return True
        else:
            logger.error("Migration may have failed - revision mismatch")
            logger.error(f"Expected: {head_rev}, Got: {new_rev}")
            return False

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        if hasattr(e, 'orig'):
            logger.error(f"Original error: {e.orig}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    success = check_migrations_and_apply()
    if not success:
        sys.exit(1)
    sys.exit(0)
