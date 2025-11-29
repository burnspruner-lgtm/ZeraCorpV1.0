import sqlite3
import logging
import threading
import os
from typing import Optional, Any, List, Dict

# --- SAFE IMPORT: POSTGRESQL ---
# We wrap this in a try/except block so the system runs locally 
# even if the production driver (psycopg2) is missing.
try:
    import psycopg2
except ImportError:
    psycopg2 = None

DB_NAME = "local_farm_data.db"

# --- DEFINE ENVIRONMENT MODE ---
# Checks if we are in production by looking for the DATABASE_URL env var
# This fixes the 'IS_PRODUCTION is not defined' error
IS_PRODUCTION = bool(os.environ.get('DATABASE_URL')) and (psycopg2 is not None)

db_local = threading.local()

class DBConnector:
    @staticmethod
    def get_db() -> Any:
        """
        Gets the database connection for the current thread.
        Uses PostgreSQL in production (if configured), SQLite locally.
        """
        conn = getattr(db_local, 'connection', None)
        if conn is None:
            try:
                # Use the module-level IS_PRODUCTION flag we just defined
                if IS_PRODUCTION:
                    logging.info("DBConnector: Connecting to Production PostgreSQL...")
                    conn = db_local.connection = psycopg2.connect(os.environ.get('DATABASE_URL'))
                else:
                    # Default Local Mode
                    logging.info("DBConnector: Connecting to local SQLite.")
                    conn = db_local.connection = sqlite3.connect(DB_NAME, check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    
            except Exception as e:
                logging.error(f"Database connection error: {e}")
                # Fallback logic is handled by the caller or by retrying in non-prod
                if not getattr(db_local, 'connection', None) and IS_PRODUCTION:
                    logging.warning("Production DB failed. Attempting emergency fallback to SQLite.")
                    try:
                        conn = db_local.connection = sqlite3.connect(DB_NAME, check_same_thread=False)
                        conn.row_factory = sqlite3.Row
                    except Exception as fallback_error:
                        logging.critical(f"Fallback failed: {fallback_error}")
                        raise e
                else:
                    raise e
        return conn

    @staticmethod
    def _connect_sqlite():
        """Helper to establish SQLite connection."""
        # This helper is kept for explicit calls if needed
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def execute_query(query: str, params: tuple = (), one: bool = False) -> Optional[Any]:
        """
        Executes a SELECT query.
        Returns dict (if one=True) or list of dicts.
        """
        try:
            conn = DBConnector.get_db()
            cursor = conn.cursor()
            
            # Check if we are actually using Postgres (psycopg2 connection object)
            is_postgres_conn = psycopg2 and isinstance(conn, psycopg2.extensions.connection)
            
            # Sanitize query parameter placeholder: SQLite uses '?', Postgres uses '%s'
            if is_postgres_conn:
                query = query.replace("?", "%s")

            cursor.execute(query, params)
            
            if is_postgres_conn:
                # --- PostgreSQL Return Logic ---
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    if one:
                        row = cursor.fetchone()
                        return dict(zip(columns, row)) if row else None
                    else:
                        rows = cursor.fetchall()
                        return [dict(zip(columns, row)) for row in rows]
                return None
            else:
                # --- SQLite Return Logic ---
                if one:
                    row = cursor.fetchone()
                    return dict(row) if row else None
                else:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"Error executing query: {e}")
            return None if one else []

    @staticmethod
    def execute_commit(query: str, params: tuple = ()) -> bool:
        """Executes an INSERT/UPDATE/DELETE query and commits."""
        try:
            conn = DBConnector.get_db()
            cursor = conn.cursor()
            
            is_postgres_conn = psycopg2 and isinstance(conn, psycopg2.extensions.connection)
            
            if is_postgres_conn:
                query = query.replace("?", "%s")

            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logging.error(f"Error executing commit: {e}")
            # SQLite does not always require rollback on simple errors, but good practice
            try:
                conn.rollback()
            except:
                pass
            return False

    @staticmethod
    def close_db(e=None):
        conn = getattr(db_local, 'connection', None)
        if conn is not None:
            conn.close()
            db_local.connection = None