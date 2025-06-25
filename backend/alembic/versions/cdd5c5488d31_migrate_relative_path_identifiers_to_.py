"""migrate_relative_path_identifiers_to_filename

Revision ID: cdd5c5488d31
Revises: 12285fde0fd3
Create Date: 2025-06-24 22:55:14.230157

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import os

# revision identifiers, used by Alembic.
revision: str = 'cdd5c5488d31'
down_revision: Union[str, None] = '12285fde0fd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate existing books where identifier equals relative_path to use filename-based identifiers
    """
    # Get connection
    connection = op.get_bind()

    # Find all records where identifier exactly matches relative_path (the old problematic behavior)
    result = connection.execute(text("""
                                     SELECT id, identifier, relative_path
                                     FROM epub_metadata
                                     WHERE identifier = relative_path
                                     """))

    records_to_update = result.fetchall()

    if not records_to_update:
        print("No records found that need identifier migration")
        return

    print(f"Found {len(records_to_update)} records where identifier = relative_path")

    # Track conflicts and updates
    conflicts = []
    successful_updates = 0

    # Process each record
    for record in records_to_update:
        record_id, old_identifier, relative_path = record

        # Extract filename from relative_path and remove extension
        filename = os.path.basename(relative_path)
        new_identifier = os.path.splitext(filename)[0]

        print(f"Processing: {old_identifier} -> {new_identifier}")

        # Check if new identifier already exists (excluding current record)
        existing_check = connection.execute(text("""
                                                 SELECT id
                                                 FROM epub_metadata
                                                 WHERE identifier = :new_id
                                                   AND id != :current_id
                                                 """), {"new_id": new_identifier, "current_id": record_id})

        if existing_check.fetchone():
            # Handle conflict by appending a numeric suffix
            counter = 1
            base_identifier = new_identifier
            while True:
                conflicted_identifier = f"{base_identifier}_{counter}"
                conflict_check = connection.execute(text("""
                                                         SELECT id
                                                         FROM epub_metadata
                                                         WHERE identifier = :new_id
                                                           AND id != :current_id
                                                         """),
                                                    {"new_id": conflicted_identifier, "current_id": record_id})

                if not conflict_check.fetchone():
                    new_identifier = conflicted_identifier
                    break
                counter += 1

                # Prevent infinite loop
                if counter > 100:
                    conflicts.append((record_id, old_identifier, relative_path))
                    print(f"ERROR: Could not resolve conflict for record {record_id}: {old_identifier}")
                    continue

            conflicts.append((record_id, old_identifier, relative_path, new_identifier))
            print(f"  Conflict resolved with suffix: {new_identifier}")

        # Update the record if we have a valid new identifier
        if new_identifier != old_identifier:
            try:
                connection.execute(text("""
                                        UPDATE epub_metadata
                                        SET identifier = :new_id
                                        WHERE id = :record_id
                                        """), {"new_id": new_identifier, "record_id": record_id})

                successful_updates += 1
                print(f"  ✓ Updated successfully")

            except Exception as e:
                print(f"  ✗ Failed to update record {record_id}: {e}")
                conflicts.append((record_id, old_identifier, relative_path, "UPDATE_FAILED"))

    print(f"\nMigration completed:")
    print(f"  - {successful_updates} records updated successfully")
    print(
        f"  - {len([c for c in conflicts if len(c) == 4 and c[3] != 'UPDATE_FAILED'])} conflicts resolved with suffixes")
    print(f"  - {len([c for c in conflicts if len(c) == 3 or c[3] == 'UPDATE_FAILED'])} failed updates")

    if conflicts:
        print(f"\nConflict details:")
        for conflict in conflicts:
            if len(conflict) == 4 and conflict[3] != "UPDATE_FAILED":
                print(f"  Resolved - ID {conflict[0]}: {conflict[1]} -> {conflict[3]}")
            elif len(conflict) == 4 and conflict[3] == "UPDATE_FAILED":
                print(f"  Failed - ID {conflict[0]}: {conflict[1]} (update failed)")
            else:
                print(f"  Unresolved - ID {conflict[0]}: {conflict[1]} (too many conflicts)")


def downgrade() -> None:
    """
    Downgrade is not supported for this data migration since we can't reliably
    reverse the identifier changes without potentially breaking existing references.
    """
    print("Downgrade not supported for this data migration")
    pass
