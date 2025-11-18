# src/db/connection.py

import os
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from src.config.settings import settings


def load_db_config():
    """Load database configuration from environment variables"""
    print("Loading DB config from environment variables")  # DEBUG

    final_cfg = {
        "host": settings.DB_HOST,
        "dbname": settings.DB_NAME,
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD,
        "port": settings.DB_PORT,
        "sslmode": settings.DB_SSLMODE,
    }

    print("DB config loaded:", final_cfg)  # DEBUG
    return final_cfg


_db_pool: SimpleConnectionPool | None = None


def init_db_pool():
    global _db_pool
    if _db_pool:
        return _db_pool

    cfg = load_db_config()

    _db_pool = SimpleConnectionPool(
        settings.DB_MINCONN,
        settings.DB_MAXCONN,
        host=cfg["host"],
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
        port=cfg["port"],
        sslmode=cfg["sslmode"],
    )

    print("DB pool initialized successfully")
    return _db_pool


@contextmanager
def get_db_conn():
    pool_obj = init_db_pool()
    conn = pool_obj.getconn()
    try:
        yield conn
    finally:
        pool_obj.putconn(conn)
