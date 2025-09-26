import os
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect
from functions.db import get_database_url
from sqlalchemy.exc import SQLAlchemyError
from config.logger import logger
import sys
from alembic.runtime.migration import MigrationContext


# Dynamically fetch the database URL
DATABASE_URL = get_database_url()


def run_cover_image_backfill(engine):
    from functions.db import get_session
    from functions.metadata.scan import save_cover_image, get_image_save_path
    from sqlalchemy import MetaData, Table, select, update
    import secrets
    from config.config import config
    logger.info("Starting cover image backfill...")

    table_name = "epub_metadata"
    id_col_name = "identifier"
    legacy_col_name = "cover_image_data"

    try:
        inspector = inspect(engine)
        if not inspector.has_table(table_name):
            logger.warning(f"Table {table_name} does not exist; nothing to backfill")
            return True
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=engine)
        missing = [c for c in (id_col_name, legacy_col_name) if c not in table.c]
        if missing:
            logger.info(f"Required column(s) missing on {table_name}: {', '.join(missing)}; nothing to backfill.")
            return True
        stmt = select(
            table.c[id_col_name],
            table.c[legacy_col_name]
        ).where(table.c[legacy_col_name].is_not(None)
        ).where(table.c.cover_image_path.is_(None))
        read_session = get_session()
        write_session = get_session()
        try:
            result = read_session.execute(
                stmt.execution_options(stream_results=True, max_row_buffer=200)
            )
            processed = 0
            for identifier, cover_image_data in result:
                token = secrets.token_urlsafe(12)[:16]
                cover_image_path = get_image_save_path(token)
                cover_image_path_posix = cover_image_path.as_posix()
                try:
                    save_cover_image(cover_image_data, cover_image_path)
                except Exception:
                    logger.exception(f"Failed to save cover image for identifier={identifier}; skipping row.")
                    continue
                try:
                    upd = (
                        update(table)
                        .where(table.c[id_col_name] == identifier)
                        .values(cover_image_path=cover_image_path_posix, cover_image_data=None)
                    )
                    write_session.execute(upd)
                except Exception:
                    logger.exception(f"DB update failed for identifier={identifier}; removing saved file.")
                    try:
                        full_image_path = os.path.join(config.COVER_BASE_DIRECTORY, cover_image_path_posix)
                        if os.path.exists(full_image_path):
                            os.remove(full_image_path)
                    except Exception:
                        logger.warning(f"Also failed to remove file {cover_image_path_posix}")
                    continue
                processed += 1
                if processed % 200 == 0:
                    write_session.flush()
                    write_session.commit()
                    logger.info(f"Processed {processed} rows...")
            write_session.commit()
            logger.info(f"Cover image backfill complete. Processed {processed} row(s).")
            return True
        except Exception:
            write_session.rollback()
            logger.exception("Error during cover image backfill; rolled back.")
            return False
        finally:
            try:
                read_session.close()
            finally:
                write_session.close()

    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        if hasattr(e, 'orig'):
            logger.error(f"Original error: {e.orig}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False


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
        try:
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            msg = str(e)
            if "BACKFILL_COVER_IMAGES_REQUIRED" in msg:
                logger.warning("Backfill required by migration; starting backfill step.")
                ok = run_cover_image_backfill(engine)
                if not ok:
                    logger.error("Backfill failed; aborting migration retry.")
                    return False
                # Retry upgrade once
                logger.info("Retrying migrations after backfill...")
                command.upgrade(alembic_cfg, "head")
            else:
                # Re-raise unexpected errors
                raise

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
    from alembic.script import ScriptDirectory

    success = check_migrations_and_apply()
    if not success:
        sys.exit(1)
    sys.exit(0)
