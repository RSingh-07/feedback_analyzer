import sqlite3
from contextlib import closing
from pathlib import Path


DB_FILE = Path(__file__).resolve().parent / "feedback.db"


def init_db() -> None:
    with closing(sqlite3.connect(DB_FILE)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY,
                    review TEXT,
                    label TEXT,
                    score INTEGER,
                    theme TEXT
                )
                """
            )


def save_results(results: list[dict[str, object]]) -> None:
    with closing(sqlite3.connect(DB_FILE)) as connection:
        with connection:
            connection.executemany(
                """
                INSERT INTO feedback (review, label, score, theme)
                VALUES (?, ?, ?, ?)
                """,
                [
                    (item["review"], item["label"], item["score"], item["theme"])
                    for item in results
                ],
            )


def load_history() -> list[dict[str, object]]:
    with closing(sqlite3.connect(DB_FILE)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, review, label, score, theme
            FROM feedback
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]
