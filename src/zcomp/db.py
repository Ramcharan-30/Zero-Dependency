import sqlite3
import datetime
from pathlib import Path

class ArchiveDatabase:
    def __init__(self, db_path: str = "zeroshrink.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS archives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_size INTEGER NOT NULL,
                    compressed_size INTEGER NOT NULL,
                    ratio REAL NOT NULL,
                    profile TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    file_path TEXT NOT NULL
                )
            ''')
            conn.commit()

    def add_archive(self, filename: str, original_size: int, compressed_size: int, profile: str, file_path: str):
        ratio = (original_size - compressed_size) / original_size * 100.0 if original_size > 0 else 0.0
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO archives (filename, original_size, compressed_size, ratio, profile, created_at, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (filename, original_size, compressed_size, ratio, profile, now, str(file_path)))
            conn.commit()

    def get_all_archives(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM archives ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]

    def delete_archive(self, archive_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM archives WHERE id = ?', (archive_id,))
            conn.commit()
