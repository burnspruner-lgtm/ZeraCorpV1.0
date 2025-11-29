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
                # Check environment to determine mode
                DATABASE_URL = os.environ.get('DATABASE_URL')
                
                # Only attempt Postgres if URL exists AND driver is present
                if DATABASE_URL and psycopg2:
                    logging.info("DBConnector: Connecting to Production PostgreSQL...")
                    conn = db_local.connection = psycopg2.connect(DATABASE_URL)
                
                elif DATABASE_URL and not psycopg2:
                    logging.error("CRITICAL: DATABASE_URL is set, but 'psycopg2' module is missing.")
                    logging.error("Falling back to SQLite to prevent crash.")
                    conn = DBConnector._connect_sqlite()
                    
                else:
                    # Default Local Mode
                    conn = DBConnector._connect_sqlite()
                    
            except Exception as e:
                logging.error(f"Database connection error: {e}")
                # Fallback to SQLite if Prod fails
                if not getattr(db_local, 'connection', None):
                    logging.warning("Attempting emergency fallback to SQLite.")
                    conn = DBConnector._connect_sqlite()
                else:
                    raise e
        return conn

    @staticmethod
    def _connect_sqlite():
        """Helper to establish SQLite connection."""
        logging.info("DBConnector: Connecting to local SQLite.")
        conn = db_local.connection = sqlite3.connect(DB_NAME, check_same_thread=False)
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
            is_postgres = psycopg2 and isinstance(conn, psycopg2.extensions.connection)
            
            # Sanitize query parameter placeholder: SQLite uses '?', Postgres uses '%s'
            if is_postgres:
                query = query.replace("?", "%s")

            cursor.execute(query, params)
            
            if is_postgres:
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
            
            is_postgres = psycopg2 and isinstance(conn, psycopg2.extensions.connection)
            
            if is_postgres:
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