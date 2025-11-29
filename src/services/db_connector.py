import sqlite3
import logging
import threading
import os
from typing import Optional, Any, List, Dict

# --- SAFE IMPORT: POSTGRESQL ---
try:
    import psycopg2
except ImportError:
    psycopg2 = None

DB_NAME = "local_farm_data.db"

# Thread-local storage for connections
db_local = threading.local()

class DBConnector:
    """
    Handles database connections securely.
    Switches between SQLite (Local) and PostgreSQL (Production) automatically.
    """

    @staticmethod
    def _is_production_mode() -> bool:
        """
        Determines if the app is running in production mode.
        Returns True only if DATABASE_URL is set AND psycopg2 driver is available.
        """
        # This function REPLACES the global variable that was causing the error
        return bool(os.environ.get('DATABASE_URL')) and (psycopg2 is not None)

    @staticmethod
    def get_db() -> Any:
        """
        Gets or creates the database connection for the current thread.
        """
        conn = getattr(db_local, 'connection', None)
        
        if conn is None:
            try:
                # Use the static method instead of a global variable
                if DBConnector._is_production_mode():
                    logging.info("DBConnector: Connecting to Production PostgreSQL...")
                    conn = db_local.connection = psycopg2.connect(os.environ.get('DATABASE_URL'))
                else:
                    logging.info("DBConnector: Connecting to local SQLite.")
                    conn = db_local.connection = sqlite3.connect(DB_NAME, check_same_thread=False)
                    conn.row_factory = sqlite3.Row
                    
            except Exception as e:
                logging.error(f"Database connection error: {e}")
                # Fallback Logic: If Prod fails, try SQLite
                if DBConnector._is_production_mode() and not getattr(db_local, 'connection', None):
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
    def execute_query(query: str, params: tuple = (), one: bool = False) -> Optional[Any]:
        """
        Executes a SELECT query safely.
        """
        try:
            conn = DBConnector.get_db()
            cursor = conn.cursor()
            
            # Detect DB Type for Syntax Sanitization
            is_postgres = False
            if psycopg2:
                # Check mode safely
                is_postgres = DBConnector._is_production_mode() and isinstance(conn, psycopg2.extensions.connection)
            
            if is_postgres:
                # Postgres uses %s, SQLite uses ?
                query = query.replace("?", "%s")

            cursor.execute(query, params)
            
            # Handle Results based on DB driver behavior
            if is_postgres:
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
                # SQLite (using row_factory)
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
        """
        Executes an INSERT/UPDATE/DELETE query and commits changes.
        """
        try:
            conn = DBConnector.get_db()
            cursor = conn.cursor()
            
            is_postgres = False
            if psycopg2:
                is_postgres = DBConnector._is_production_mode() and isinstance(conn, psycopg2.extensions.connection)
            
            if is_postgres:
                query = query.replace("?", "%s")

            cursor.execute(query, params)
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            logging.error(f"Error executing commit: {e}")
            try:
                conn.rollback()
            except:
                pass
            return False

    @staticmethod
    def close_db(e=None):
        """Closes the thread-local connection."""
        conn = getattr(db_local, 'connection', None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
            db_local.connection = None