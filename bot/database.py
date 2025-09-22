import sqlite3
import os
from contextlib import contextmanager


class Database:
    def __init__(self, db_url):
        if db_url.startswith('sqlite:///'):
            db_path = db_url[10:]
        else:
            db_path = db_url

        # Создаем абсолютный путь
        self.db_path = os.path.abspath(db_path)

        # Создаем директорию для базы данных если нужно
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Если путь содержит директории
            os.makedirs(db_dir, exist_ok=True)

        print(f"База данных будет создана по пути: {self.db_path}")
        self.init_db()

    def init_db(self):
        try:
            with self.get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        chat_id INTEGER UNIQUE NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS websites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        url TEXT NOT NULL,
                        user_id INTEGER NOT NULL,
                        check_interval INTEGER DEFAULT 300,
                        last_status TEXT DEFAULT 'unknown',
                        last_response_time REAL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS check_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        website_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        status_code INTEGER,
                        response_time REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (website_id) REFERENCES websites (id)
                    )
                ''')
                conn.commit()
                print("База данных успешно инициализирована")
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {e}")
            raise

    @contextmanager
    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            except Exception as e:
                conn.rollback()
                print(f"Ошибка в транзакции: {e}")
                raise
            finally:
                conn.close()
        except sqlite3.Error as e:
            print(f"Ошибка подключения к базе данных: {e}")
            print(f"Путь к базе: {self.db_path}")
            raise

    def add_user(self, user_id, chat_id):
        with self.get_connection() as conn:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO users (id, chat_id) VALUES (?, ?)",
                    (user_id, chat_id)
                )
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении пользователя: {e}")
                return False

    def add_website(self, user_id, url, interval):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO websites (url, user_id, check_interval, last_status) VALUES (?, ?, ?, ?)",
                    (url, user_id, interval, 'unknown')
                )
                conn.commit()
                return cursor.lastrowid
            except sqlite3.Error as e:
                print(f"Ошибка при добавлении сайта: {e}")
                return None

    def get_user_websites(self, user_id):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM websites WHERE user_id = ? AND is_active = TRUE",
                    (user_id,)
                )
                return cursor.fetchall()
            except sqlite3.Error as e:
                print(f"Ошибка при получении сайтов: {e}")
                return []

    def delete_website(self, user_id, website_id):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE websites SET is_active = FALSE WHERE id = ? AND user_id = ?",
                    (website_id, user_id)
                )
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.Error as e:
                print(f"Ошибка при удалении сайта: {e}")
                return False

    def get_website_stats(self, website_id):
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()

                # Общая статистика
                cursor.execute(
                    "SELECT COUNT(*) as total_checks, "
                    "SUM(CASE WHEN status = 'up' THEN 1 ELSE 0 END) as up_checks, "
                    "AVG(response_time) as avg_response_time "
                    "FROM check_results WHERE website_id = ?",
                    (website_id,)
                )
                return cursor.fetchone()
            except sqlite3.Error as e:
                print(f"Ошибка при получении статистики: {e}")
                return None