import sqlite3
import os
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name="lungeguard.db"):
        """
        Manager lokalnej bazy danych SQLite.
        Automatycznie tworzy strukturę tabel przy inicjalizacji.
        """
        # Upewniamy się, że folder database istnieje
        self.db_folder = "database"
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)

        self.db_path = os.path.join(self.db_folder, db_name)
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def create_tables(self):
        """Tworzy strukturę bazy danych (Relacyjna)."""
        query_users = """
                      CREATE TABLE IF NOT EXISTS users \
                      ( \
                          id \
                          INTEGER \
                          PRIMARY \
                          KEY \
                          AUTOINCREMENT, \
                          name \
                          TEXT \
                          UNIQUE \
                          NOT \
                          NULL, \
                          created_at \
                          TIMESTAMP \
                          DEFAULT \
                          CURRENT_TIMESTAMP
                      ); \
                      """

        query_sessions = """
                         CREATE TABLE IF NOT EXISTS sessions \
                         ( \
                             id \
                             INTEGER \
                             PRIMARY \
                             KEY \
                             AUTOINCREMENT, \
                             user_id \
                             INTEGER, \
                             start_time \
                             TIMESTAMP, \
                             end_time \
                             TIMESTAMP, \
                             reps \
                             INTEGER \
                             DEFAULT \
                             0, \
                             FOREIGN \
                             KEY \
                         ( \
                             user_id \
                         ) REFERENCES users \
                         ( \
                             id \
                         )
                             ); \
                         """

        query_errors = """
                       CREATE TABLE IF NOT EXISTS error_logs \
                       ( \
                           id \
                           INTEGER \
                           PRIMARY \
                           KEY \
                           AUTOINCREMENT, \
                           session_id \
                           INTEGER, \
                           error_type \
                           TEXT, \
                           timestamp \
                           TIMESTAMP \
                           DEFAULT \
                           CURRENT_TIMESTAMP, \
                           FOREIGN \
                           KEY \
                       ( \
                           session_id \
                       ) REFERENCES sessions \
                       ( \
                           id \
                       )
                           ); \
                       """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_users)
            cursor.execute(query_sessions)
            cursor.execute(query_errors)

    # --- METODY UŻYTKOWNIKA ---

    def add_user(self, name):
        """Dodaje nowego użytkownika."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Użytkownik już istnieje

    def get_users(self):
        """Pobiera listę wszystkich użytkowników."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM users")
            return cursor.fetchall()

    # --- METODY TRENINGOWE ---

    def start_session(self, user_id):
        """Rozpoczyna nowy trening."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("INSERT INTO sessions (user_id, start_time, reps) VALUES (?, ?, 0)",
                           (user_id, now))
            return cursor.lastrowid  # Zwraca ID sesji

    def end_session(self, session_id, total_reps):
        """Kończy trening i zapisuje wynik."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("UPDATE sessions SET end_time = ?, reps = ? WHERE id = ?",
                           (now, total_reps, session_id))

    def log_error(self, session_id, error_type):
        """Zapisuje wystąpienie błędu (np. 'Valgus')."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute("INSERT INTO error_logs (session_id, error_type, timestamp) VALUES (?, ?, ?)",
                           (session_id, error_type, now))

    def get_user_history(self, user_id):
        """Pobiera historię treningów danego użytkownika."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                    SELECT s.start_time, s.reps, COUNT(e.id) as error_count
                    FROM sessions s
                             LEFT JOIN error_logs e ON s.id = e.session_id
                    WHERE s.user_id = ?
                    GROUP BY s.id
                    ORDER BY s.start_time DESC \
                    """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()