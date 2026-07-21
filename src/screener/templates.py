"""
templates.py

Custom screen template management for the Investment Screener Engine (Module 6).
Handles saving, loading, and deleting custom screener definitions in SQLite.
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.config.logging_config import get_logger
from src.database.connection import get_connection
from src.screener.constants import SCREEN_TEMPLATES_TABLE

logger = get_logger(__name__)


# =============================================================================
# SCREEN TEMPLATE MANAGER
# =============================================================================

class ScreenTemplateManager:
    """
    Manages custom screen templates in the database.

    Provides CRUD operations for saving, loading, and deleting
    custom screener definitions.
    """

    def __init__(self):
        """Initialize the ScreenTemplateManager."""
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Create the screen_templates table if it doesn't exist."""
        try:
            conn = get_connection()
            schema = f"""
                CREATE TABLE IF NOT EXISTS {SCREEN_TEMPLATES_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    filters TEXT NOT NULL,
                    sort_by TEXT,
                    sort_order TEXT DEFAULT 'asc',
                    rank_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            conn.execute(schema)
            conn.commit()
            logger.info(f"Ensured {SCREEN_TEMPLATES_TABLE} table exists")
        except Exception as e:
            logger.error(f"Failed to create {SCREEN_TEMPLATES_TABLE} table: {str(e)}")
            raise

    def save_screen(
        self,
        name: str,
        filters: List[Dict[str, Any]],
        description: str = "",
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        rank_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Save a custom screen template to the database.

        Parameters
        ----------
        name : str
            Unique name for the screen template
        filters : List[Dict[str, Any]]
            List of filter conditions
        description : str, optional
            Description of the screen template
        sort_by : str, optional
            Field to sort by
        sort_order : str, optional
            Sort order: "asc" or "desc", by default "asc"
        rank_by : str, optional
            Field to rank by

        Returns
        -------
        Dict[str, Any]
            Result with 'success', 'id', and 'message'

        Raises
        ------
        ValueError
            If name is empty or filters is empty
        """
        if not name or not name.strip():
            raise ValueError("Screen template name cannot be empty")

        if not filters:
            raise ValueError("Screen template must have at least one filter")

        if sort_order not in ("asc", "desc"):
            raise ValueError(f"sort_order must be 'asc' or 'desc', got '{sort_order}'")

        try:
            conn = get_connection()
            cursor = conn.cursor()

            # Serialize filters to JSON
            filters_json = json.dumps(filters)

            # Check if template already exists (update)
            cursor.execute(
                f"SELECT id FROM {SCREEN_TEMPLATES_TABLE} WHERE name = ?",
                (name,),
            )
            existing = cursor.fetchone()

            now = datetime.now().isoformat()

            if existing:
                # Update existing template
                cursor.execute(
                    f"""
                    UPDATE {SCREEN_TEMPLATES_TABLE}
                    SET description = ?, filters = ?, sort_by = ?,
                        sort_order = ?, rank_by = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        description,
                        filters_json,
                        sort_by,
                        sort_order,
                        rank_by,
                        now,
                        existing["id"],
                    ),
                )
                template_id = existing["id"]
                message = f"Updated screen template '{name}' (ID: {template_id})"
                logger.info(message)
            else:
                # Insert new template
                cursor.execute(
                    f"""
                    INSERT INTO {SCREEN_TEMPLATES_TABLE}
                    (name, description, filters, sort_by, sort_order, rank_by, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        description,
                        filters_json,
                        sort_by,
                        sort_order,
                        rank_by,
                        now,
                        now,
                    ),
                )
                template_id = cursor.lastrowid
                message = f"Saved screen template '{name}' (ID: {template_id})"
                logger.info(message)

            conn.commit()

            return {
                "success": True,
                "id": template_id,
                "message": message,
            }

        except sqlite3.IntegrityError as e:
            error_msg = f"Integrity error saving screen template '{name}': {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "id": None,
                "message": error_msg,
            }
        except Exception as e:
            error_msg = f"Failed to save screen template '{name}': {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "id": None,
                "message": error_msg,
            }

    def load_screen(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a custom screen template by name.

        Parameters
        ----------
        name : str
            Name of the screen template to load

        Returns
        -------
        Optional[Dict[str, Any]]
            Screen template definition, or None if not found
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT id, name, description, filters, sort_by, sort_order, rank_by,
                       created_at, updated_at
                FROM {SCREEN_TEMPLATES_TABLE}
                WHERE name = ?
                """,
                (name,),
            )
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Screen template '{name}' not found")
                return None

            # Deserialize filters from JSON
            filters = json.loads(row["filters"])

            template = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "filters": filters,
                "sort_by": row["sort_by"],
                "sort_order": row["sort_order"],
                "rank_by": row["rank_by"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

            logger.info(f"Loaded screen template '{name}' (ID: {row['id']})")
            return template

        except Exception as e:
            error_msg = f"Failed to load screen template '{name}': {str(e)}"
            logger.error(error_msg)
            return None

    def load_screen_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """
        Load a custom screen template by ID.

        Parameters
        ----------
        template_id : int
            ID of the screen template to load

        Returns
        -------
        Optional[Dict[str, Any]]
            Screen template definition, or None if not found
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT id, name, description, filters, sort_by, sort_order, rank_by,
                       created_at, updated_at
                FROM {SCREEN_TEMPLATES_TABLE}
                WHERE id = ?
                """,
                (template_id,),
            )
            row = cursor.fetchone()

            if not row:
                logger.warning(f"Screen template with ID {template_id} not found")
                return None

            # Deserialize filters from JSON
            filters = json.loads(row["filters"])

            template = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "filters": filters,
                "sort_by": row["sort_by"],
                "sort_order": row["sort_order"],
                "rank_by": row["rank_by"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

            logger.info(f"Loaded screen template ID {template_id} ('{row['name']}')")
            return template

        except Exception as e:
            error_msg = f"Failed to load screen template ID {template_id}: {str(e)}"
            logger.error(error_msg)
            return None

    def delete_screen(self, name: str) -> Dict[str, Any]:
        """
        Delete a custom screen template by name.

        Parameters
        ----------
        name : str
            Name of the screen template to delete

        Returns
        -------
        Dict[str, Any]
            Result with 'success' and 'message'
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM {SCREEN_TEMPLATES_TABLE} WHERE name = ?",
                (name,),
            )

            if cursor.rowcount == 0:
                message = f"Screen template '{name}' not found"
                logger.warning(message)
                return {"success": False, "message": message}

            conn.commit()
            message = f"Deleted screen template '{name}'"
            logger.info(message)
            return {"success": True, "message": message}

        except Exception as e:
            error_msg = f"Failed to delete screen template '{name}': {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    def delete_screen_by_id(self, template_id: int) -> Dict[str, Any]:
        """
        Delete a custom screen template by ID.

        Parameters
        ----------
        template_id : int
            ID of the screen template to delete

        Returns
        -------
        Dict[str, Any]
            Result with 'success' and 'message'
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"DELETE FROM {SCREEN_TEMPLATES_TABLE} WHERE id = ?",
                (template_id,),
            )

            if cursor.rowcount == 0:
                message = f"Screen template with ID {template_id} not found"
                logger.warning(message)
                return {"success": False, "message": message}

            conn.commit()
            message = f"Deleted screen template ID {template_id}"
            logger.info(message)
            return {"success": True, "message": message}

        except Exception as e:
            error_msg = f"Failed to delete screen template ID {template_id}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "message": error_msg}

    def list_screens(self) -> List[Dict[str, Any]]:
        """
        List all custom screen templates.

        Returns
        -------
        List[Dict[str, Any]]
            List of screen template summaries
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT id, name, description, filters, sort_by, sort_order, rank_by,
                       created_at, updated_at
                FROM {SCREEN_TEMPLATES_TABLE}
                ORDER BY updated_at DESC
                """
            )
            rows = cursor.fetchall()

            templates = []
            for row in rows:
                # Count filters from JSON
                try:
                    filters = json.loads(row["filters"])
                    filter_count = len(filters)
                except (json.JSONDecodeError, TypeError):
                    filter_count = 0

                templates.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "filter_count": filter_count,
                    "sort_by": row["sort_by"],
                    "sort_order": row["sort_order"],
                    "rank_by": row["rank_by"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                })

            logger.info(f"Listed {len(templates)} screen templates")
            return templates

        except Exception as e:
            error_msg = f"Failed to list screen templates: {str(e)}"
            logger.error(error_msg)
            return []

    def get_screen_count(self) -> int:
        """
        Get the total number of custom screen templates.

        Returns
        -------
        int
            Number of screen templates
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(f"SELECT COUNT(*) FROM {SCREEN_TEMPLATES_TABLE}")
            count = cursor.fetchone()[0]

            return count

        except Exception as e:
            logger.error(f"Failed to get screen template count: {str(e)}")
            return 0