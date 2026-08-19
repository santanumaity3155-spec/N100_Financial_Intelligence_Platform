"""
connection.py

Database connection manager for the
N100 Financial Intelligence Platform.

Responsibilities
----------------
1. Create SQLite database connection
2. Create database directory if missing
3. Enable Foreign Key support
4. Provide helper functions
5. Safe connection closing
"""

import threading
import sqlite3
from pathlib import Path
from typing import Optional

from src.config.constants import DATABASE_DIR
from src.config.settings import SQLITE_DATABASE
from src.config.logging_config import get_logger

logger = get_logger(__name__)


class DatabaseConnection:
    """
    SQLite Database Connection Manager (Thread-Safe)
    """

    def __init__(self):
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        self.database_path = SQLITE_DATABASE
        self._local = threading.local()

    @property
    def connection(self) -> Optional[sqlite3.Connection]:
        """
        Get the thread-local SQLite connection.
        """
        return getattr(self._local, "conn", None)

    @connection.setter
    def connection(self, val: Optional[sqlite3.Connection]):
        self._local.conn = val

    def connect(self) -> sqlite3.Connection:
        """
        Establish thread-local database connection.

        Returns
        -------
        sqlite3.Connection
        """
        conn = self.connection
        if conn is not None:
            try:
                conn.execute("SELECT 1")
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                conn = None

        if conn is None:
            try:
                conn = sqlite3.connect(
                    self.database_path,
                    check_same_thread=False,
                    timeout=30.0
                )
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON;")
                self.connection = conn
                logger.info(
                    f"Connected to SQLite database (thread-safe): {self.database_path}"
                )
            except sqlite3.Error as e:
                logger.exception("Failed to connect to database")
                raise e

        return conn

    def enable_foreign_keys(self):
        """
        Enable SQLite Foreign Key Constraints.
        """
        conn = self.connect()
        conn.execute("PRAGMA foreign_keys = ON;")
        logger.info("Foreign Keys Enabled")

    def get_cursor(self) -> sqlite3.Cursor:
        """
        Returns SQLite Cursor for current thread.
        """
        return self.connect().cursor()

    def commit(self):
        """
        Commit pending transactions for current thread.
        """
        conn = self.connection
        if conn:
            conn.commit()
            logger.info("Transaction Committed")

    def rollback(self):
        """
        Rollback transaction for current thread.
        """
        conn = self.connection
        if conn:
            conn.rollback()
            logger.warning("Transaction Rolled Back")

    def close(self):
        """
        Close database connection for current thread.
        """
        conn = self.connection
        if conn:
            conn.close()
            logger.info("Database Connection Closed")
            self.connection = None


# -----------------------------------------------------
# Singleton Connection Object
# -----------------------------------------------------

db = DatabaseConnection()


# -----------------------------------------------------
# Utility Functions
# -----------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """
    Returns active database connection.
    """

    return db.connect()


def get_cursor() -> sqlite3.Cursor:
    """
    Returns active cursor.
    """

    return db.get_cursor()


def commit():
    """
    Commit transaction.
    """

    db.commit()


def rollback():
    """
    Rollback transaction.
    """

    db.rollback()


def close_connection():
    """
    Close active connection.
    """

    db.close()


# -----------------------------------------------------
# Script Test
# -----------------------------------------------------

if __name__ == "__main__":

    conn = get_connection()

    print("Database Connected Successfully")

    close_connection()