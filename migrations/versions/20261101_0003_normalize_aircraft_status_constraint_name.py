"""Normalize the aircraft status check-constraint name.

Revision ID: 20261101_0003
Revises: 20261101_0002
Create Date: 2026-11-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20261101_0003"
down_revision: str | None = "20261101_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Converge historical and canonical constraint names safely."""
    op.execute(
        """
        DO $$
        DECLARE
            old_exists boolean;
            final_exists boolean;
        BEGIN
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conrelid = 'aircraft'::regclass
                  AND conname = 'ck_aircraft_ck_aircraft_status'
            )
            INTO old_exists;

            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conrelid = 'aircraft'::regclass
                  AND conname = 'ck_aircraft_status'
            )
            INTO final_exists;

            IF old_exists AND NOT final_exists THEN
                ALTER TABLE aircraft
                    RENAME CONSTRAINT ck_aircraft_ck_aircraft_status
                    TO ck_aircraft_status;
            ELSIF old_exists AND final_exists THEN
                ALTER TABLE aircraft
                    DROP CONSTRAINT ck_aircraft_ck_aircraft_status;
            ELSIF NOT old_exists AND final_exists THEN
                NULL;
            ELSE
                RAISE EXCEPTION
                    'aircraft status check constraint is missing; '
                    'expected ck_aircraft_status or ck_aircraft_ck_aircraft_status';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    """Restore the historical name while tolerating either starting state."""
    op.execute(
        """
        DO $$
        DECLARE
            old_exists boolean;
            final_exists boolean;
        BEGIN
            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conrelid = 'aircraft'::regclass
                  AND conname = 'ck_aircraft_ck_aircraft_status'
            )
            INTO old_exists;

            SELECT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conrelid = 'aircraft'::regclass
                  AND conname = 'ck_aircraft_status'
            )
            INTO final_exists;

            IF final_exists AND NOT old_exists THEN
                ALTER TABLE aircraft
                    RENAME CONSTRAINT ck_aircraft_status
                    TO ck_aircraft_ck_aircraft_status;
            ELSIF final_exists AND old_exists THEN
                ALTER TABLE aircraft
                    DROP CONSTRAINT ck_aircraft_status;
            ELSIF old_exists AND NOT final_exists THEN
                NULL;
            ELSE
                RAISE EXCEPTION
                    'aircraft status check constraint is missing; '
                    'expected ck_aircraft_status or ck_aircraft_ck_aircraft_status';
            END IF;
        END
        $$;
        """
    )
