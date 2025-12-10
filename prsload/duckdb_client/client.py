import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field

import duckdb

logger = logging.getLogger(__name__)

# Use a file-based DuckDB for persistence
DB_FILE_PATH = "prs_analytics.duckdb"


def get_connection_obj():
    return duckdb.connect(database=DB_FILE_PATH)


@contextmanager
def get_connection():
    conn = get_connection_obj()
    try:
        yield conn
    finally:
        conn.close()


# Table definitions
TABLE_SCHEMAS = {
    "prs": """
        CREATE TABLE IF NOT EXISTS prs (
            id INTEGER PRIMARY KEY DEFAULT nextval('prs_id_seq'),
            number INTEGER,
            repo_slug VARCHAR,
            title VARCHAR,
            url VARCHAR,
            author VARCHAR,
            created_at TIMESTAMP,
            merged_at TIMESTAMP,
            UNIQUE(repo_slug, number)
        )
    """,
    "reviews": """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY DEFAULT nextval('reviews_id_seq'),
            pr_id INTEGER,
            reviewer VARCHAR,
            requested_at TIMESTAMP,
            first_sign_of_life TIMESTAMP,
            first_approve_or_disapprove TIMESTAMP,
            FOREIGN KEY (pr_id) REFERENCES prs(id)
        )
    """,
}


def create_tables():
    """Create all required DuckDB tables."""
    with get_connection() as conn:
        # Create sequences first
        conn.execute("CREATE SEQUENCE IF NOT EXISTS prs_id_seq")
        conn.execute("CREATE SEQUENCE IF NOT EXISTS reviews_id_seq")

        for table_name, schema in TABLE_SCHEMAS.items():
            conn.execute(schema)
            logger.debug(f"Created/verified table: {table_name}")

        logger.info("All DuckDB tables created/verified")


def recreate_tables():
    """Drop the database file and recreate all tables."""

    # Close any existing connections by creating a temporary one and closing it
    with get_connection():
        pass

    if os.path.exists(DB_FILE_PATH):
        os.remove(DB_FILE_PATH)
        logger.debug(f"Deleted database file: {DB_FILE_PATH}")

    create_tables()


@dataclass
class HealthState:
    status: str
    tables: list[str] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    error_msg: str = field(default="")

    @property
    def database_file(self) -> str:
        return DB_FILE_PATH


def health_check() -> HealthState:
    """Check DuckDB connection and basic functionality."""
    with get_connection() as conn:
        try:
            # Test basic query
            result = conn.execute("SELECT 1 as test").fetchone()
            test_passed = result[0] == 1

            create_tables()

            tables = conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()

            table_names: list[str] = [table[0] for table in tables]

            row_counts: dict[str, int] = {}
            for table_name in ["prs", "reviews"]:
                if table_name in table_names:
                    count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    row_counts[table_name] = count

            return HealthState(
                status="healthy" if test_passed else "error",
                tables=table_names,
                row_counts=row_counts,
            )

        except Exception as e:
            return HealthState(status="error", error_msg=str(e))
