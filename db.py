"""
Local storage for analyzed inquiries, using SQLite.

SQLite keeps everything in a single file (inquiries.db) that lives right
next to the app - there's no separate database server to install or
run, which is why it's a good fit for a small local tool like this one.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "inquiries.db"


@contextmanager
def get_connection():
    """
    Open a database connection, make rows come back as dictionaries
    instead of plain tuples, and always close the connection when we're
    done - even if something raises an error along the way.
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def init_db():
    """
    Create the inquiries table if it doesn't exist yet.

    This is safe to call every time the app starts: "CREATE TABLE IF NOT
    EXISTS" does nothing when the table is already there.
    """
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                source_message TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                order_number TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                customer_request TEXT NOT NULL,
                recommended_next_step TEXT NOT NULL,
                suggested_department TEXT NOT NULL,
                suggested_response TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending Review'
            )
            """
        )
        connection.commit()


def save_inquiry(source_message: str, result: dict) -> int:
    """Save one analyzed inquiry as 'Pending Review' and return its new id."""
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO inquiries (
                created_at, source_message, category, priority, customer_name,
                order_number, sentiment, customer_request, recommended_next_step,
                suggested_department, suggested_response, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                source_message,
                result["category"],
                result["priority"],
                result["customer_name"],
                result["order_number"],
                result["sentiment"],
                result["customer_request"],
                result["recommended_next_step"],
                result["suggested_department"],
                result["suggested_response"],
                "Pending Review",
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_recent_inquiries(limit: int = 20):
    """Return the most recently created inquiries, newest first."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM inquiries ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def update_status(inquiry_id: int, status: str) -> None:
    """Change one inquiry's status - for example, to 'Approved'."""
    with get_connection() as connection:
        connection.execute(
            "UPDATE inquiries SET status = ? WHERE id = ?", (status, inquiry_id)
        )
        connection.commit()


def update_inquiry(inquiry_id: int, fields: dict, status: str) -> None:
    """
    Save the human-edited version of an inquiry and set its new status.

    This runs when someone reviews the AI's suggestions, fixes anything
    that's wrong, and clicks Approve (or Dismiss). The AI's original
    guess is overwritten with whatever the human confirmed - the human's
    decision is what the record should reflect from then on.
    """
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE inquiries
            SET category = ?, priority = ?, customer_name = ?, order_number = ?,
                sentiment = ?, customer_request = ?, recommended_next_step = ?,
                suggested_department = ?, suggested_response = ?, status = ?
            WHERE id = ?
            """,
            (
                fields["category"],
                fields["priority"],
                fields["customer_name"],
                fields["order_number"],
                fields["sentiment"],
                fields["customer_request"],
                fields["recommended_next_step"],
                fields["suggested_department"],
                fields["suggested_response"],
                status,
                inquiry_id,
            ),
        )
        connection.commit()


def get_category_counts():
    """Return {category: count} across every saved inquiry - used by the dashboard."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT category, COUNT(*) AS total FROM inquiries GROUP BY category"
        ).fetchall()
        return {row["category"]: row["total"] for row in rows}


def get_priority_counts():
    """Return {priority: count} across every saved inquiry - used by the dashboard."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT priority, COUNT(*) AS total FROM inquiries GROUP BY priority"
        ).fetchall()
        return {row["priority"]: row["total"] for row in rows}


def get_status_counts():
    """Return {status: count} across every saved inquiry - used by the dashboard."""
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT status, COUNT(*) AS total FROM inquiries GROUP BY status"
        ).fetchall()
        return {row["status"]: row["total"] for row in rows}


def get_total_count() -> int:
    """Return how many inquiries have ever been analyzed."""
    with get_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM inquiries").fetchone()
        return row["total"]
