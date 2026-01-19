import sqlite3
import os
import json
from datetime import datetime


class DatabaseManager:
    """Manager lokalnej bazy danych SQLite dla aplikacji LungeGuard."""

    def __init__(self, db_name="lungeguard.db"):
        self.db_folder = "database"
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

        self.db_path = os.path.join(self.db_folder, db_name)
        self.create_tables()
        self._migrate_tables()

    def get_connection(self):
        """Tworzy i zwraca połączenie z bazą danych."""
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        """Inicjalizuje strukturę tabel w bazie danych."""
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        query_sessions = """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            reps INTEGER DEFAULT 0,
            video_path TEXT,
            graph_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """

        query_errors = """
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            error_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (id)
        );
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_users)
            cursor.execute(query_sessions)
            cursor.execute(query_errors)

    def _migrate_tables(self):
        """Aktualizacja struktury bazy danych dla zgodności ze starszymi wersjami."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN video_path TEXT")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje

        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN graph_data TEXT")
        except sqlite3.OperationalError:
            pass  # Kolumna już istnieje

        conn.commit()
        conn.close()

    def add_user(self, name):
        """Rejestruje nowego użytkownika w systemie."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_users(self):
        """Pobiera listę wszystkich zarejestrowanych użytkowników."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM users")
            return cursor.fetchall()

    def start_session(self, user_id):
        """Inicjuje nową sesję treningową dla użytkownika."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("INSERT INTO sessions (user_id, start_time, reps) VALUES (?, ?, 0)", (user_id, now))
            return cursor.lastrowid

    def end_session(self, session_id, total_reps, video_path=None, graph_data_dict=None):
        """Zamyka sesję treningową, zapisując końcowe wyniki i dane analityczne."""
        graph_json = None
        if graph_data_dict:
            try:
                graph_json = json.dumps(graph_data_dict)
            except (TypeError, ValueError):
                pass

        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("""
                UPDATE sessions
                SET end_time   = ?,
                    reps       = ?,
                    video_path = ?,
                    graph_data = ?
                WHERE id = ?
            """, (now, total_reps, video_path, graph_json, session_id))

    def log_error(self, session_id, error_type):
        """Zapisuje wystąpienie błędu technicznego podczas sesji."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("INSERT INTO error_logs (session_id, error_type, timestamp) VALUES (?, ?, ?)",
                           (session_id, error_type, now))

    def get_user_history(self, user_id):
        """Pobiera pełną historię sesji użytkownika wraz z błędami i ścieżkami do nagrań."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
            SELECT s.start_time, s.reps, COUNT(e.id) as error_count, s.video_path, s.graph_data
            FROM sessions s
            LEFT JOIN error_logs e ON s.id = e.session_id
            WHERE s.user_id = ?
            GROUP BY s.id
            ORDER BY s.start_time DESC
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()