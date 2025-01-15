import os
import threading
import time
import json
import sys
from flask import Flask
from models.epub_metadata import EpubMetadata
from functions.db import get_session
from functions.metadata.scan import scan_and_store_metadata, find_epubs
from functions.utils import check_admin_user, reset_admin_user_password, check_required_envs
from config.config import config
from config.logger import logger
from filelock import FileLock

def create_app():
    app = Flask(__name__, static_folder="../frontend/dist", static_url_path="/static")

    app.config["RATELIMIT_ENABLED"] = config.RATE_LIMITER_ENABLED
    app.config["RATELIMIT_STORAGE_URI"] = config.RATE_LIMITER_URI

    lock_file_path = "./scan_lock.lock"
    last_scan_file_path = "./last_scan_time.json"

    try:
        result, message = check_required_envs(config.SECRET_KEY, config.BASE_URL)
        if not result:
            logger.error(message)
            sys.exit(1)
        else:
            logger.debug("Required environment variables checked successfully.")
    except Exception as e:
        logger.exception("Failed to check required environment variables: %s", str(e))
        sys.exit(1)

    if config.ENVIRONMENT != "test":
        try:
            result, message = check_admin_user(config.ADMIN_PASS, config.ADMIN_EMAIL)
            if not result:
                logger.error("Failed to initialize admin user: %s", message)
                sys.exit(1)
            else:
                logger.info("Admin user initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize admin user: %s", str(e))
            sys.exit(1)
    else:
        print("TEST ENVIRONMENT")

    if config.ADMIN_RESET:
        try:
            result, message = reset_admin_user_password(config.ADMIN_PASS)
            if not result:
                logger.error("Failed to reset admin user password: %s", message)
                sys.exit(1)
        except Exception as e:
            logger.exception("Failed to reset admin user password: %s", str(e))


    def get_last_scan_time():
        """Read the last scan time from a shared file, defaulting to 0 if not set."""
        if not os.path.exists(last_scan_file_path):
            return 0  # No scan has been performed yet

        try:
            with open(last_scan_file_path, "r") as f:
                data = json.load(f)
                return data.get("last_scan_time", 0)  # Ensure backward compatibility
        except (IOError, ValueError, json.JSONDecodeError):
            return 0  # If the file is corrupted or empty, reset to 0


    def set_last_scan_time(timestamp):
        """Write the last scan time to the shared file."""
        temp_file_path = f"{last_scan_file_path}.tmp"  # Write to a temporary file first
        try:
            with open(temp_file_path, "w") as f:
                json.dump({"last_scan_time": timestamp}, f)
            os.replace(temp_file_path, last_scan_file_path)  # Atomically replace the file
        except IOError as e:
            logger.error(f"Failed to write last scan time: {e}")

    def background_scan():
        """
        Perform the scanning of the library in a separate thread.
        Ensure that only one scan runs at a time.
        """

        try:
            # Perform the scan
            base_directory = config.BASE_DIRECTORY
            logger.debug("Background scan started. Base directory: " + base_directory)

            epubs = find_epubs(base_directory)
            epub_length = int(len(epubs))
            logger.debug("Found " + str(epub_length) + " ePub files in " + base_directory)

            session = get_session()
            db_epub_count = int(session.query(EpubMetadata).count())
            logger.debug("Found " + str(db_epub_count) + " books in database.")

            if db_epub_count != epub_length:
                logger.info("Changes detected between database and filesystem. Running scan...")
                scan_and_store_metadata(base_directory)
                logger.info("Library scan complete.")
            else:
                logger.debug("No changes between database and filesystem. Scan skipped.")

        except Exception as e:
            logger.error("Error during background scan: %s", str(e))

        finally:
            # Ensure that the scanner state is reset, even if something fails
            logger.debug("Background scan finished.")

    @app.before_request
    def scan_library_for_changes():
        # Use a file-based lock to synchronize between workers
        lock = FileLock(lock_file_path)

        try:
            # Try acquiring the lock
            with lock.acquire(timeout=10):  # Wait max 10 seconds for the lock
                #logger.debug("Acquired file lock for scanning.")
                if config.ENVIRONMENT == "test":
                    #logger.debug("In testing environment, skipping scan")
                    return None

                # Atomically read/write shared `last_scan_time`
                current_time = time.time()
                last_scan_time = get_last_scan_time()

                if current_time - last_scan_time < 5:  # Adjust timer as needed
                    logger.debug("Scan skipped: Triggered too soon after the last scan.")
                    return None

                # Update last scan time to prevent other workers from triggering
                set_last_scan_time(current_time)
                # Start scan in a background thread
                thread = threading.Thread(target=background_scan)
                thread.daemon = True  # Ensure the thread exits with the process
                thread.start()

        except TimeoutError:
            logger.debug("Another worker is already running the scan. Skipping.")

    return app