import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Any, Optional
import logging

from .config import config

logger = logging.getLogger(__name__)

class Database:
    _pool: Optional[pool.ThreadedConnectionPool] = None

    @classmethod
    def initialize(cls):
        if cls._pool is None:
            cls._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                dsn=config.postgres_dsn
            )
            logger.info("Database pool initialized")

    @classmethod
    def close(cls):
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            logger.info("Database pool closed")

    @classmethod
    @contextmanager
    def get_connection(cls):
        if cls._pool is None:
            cls.initialize()
        conn = cls._pool.getconn()
        try:
            yield conn
        finally:
            cls._pool.putconn(conn)

    @classmethod
    @contextmanager
    def get_cursor(cls, dict_cursor: bool = True):
        with cls.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    @classmethod
    def execute(cls, query: str, params: tuple = None) -> list[dict]:
        with cls.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    @classmethod
    def execute_one(cls, query: str, params: tuple = None) -> Optional[dict]:
        with cls.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    @classmethod
    def insert_one(cls, table: str, data: dict) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        result = cls.execute_one(query, tuple(data.values()))
        return result["id"] if result else None

    @classmethod
    def table_exists(cls, table_name: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """
        result = cls.execute_one(query, (table_name,))
        return result["exists"] if result else False

db = Database()
