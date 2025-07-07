import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Corrected path for .env file, assuming it's in the project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATABASE_URL_ROOT = os.getenv("DATABASE_URL_ROOT") 
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL_ROOT:
    raise ValueError("DATABASE_URL_ROOT environment variable is not set. Please check your .env file.")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please check your .env file.")

def get_DB_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise Exception(f"Could not connect to the database: {e}") # Re-raising as generic Exception to be caught by HTTPException in API

# --- Database Initialization on Startup ---
async def initialize_database():
    print("Attempting to initialize database and tables...")

    conn_root = None
    cur_root = None
    try:
        conn_root = psycopg2.connect(DATABASE_URL_ROOT)
        conn_root.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur_root = conn_root.cursor()

        # Keeping 'waytoo' as the database name as per your provided code
        cur_root.execute("SELECT 1 FROM pg_database WHERE datname = 'waytoo'")
        if not cur_root.fetchone():
            print("Database 'waytoo' not found. Creating it...")
            cur_root.execute("CREATE DATABASE waytoo")
            print("Database 'waytoo' created successfully.")
        else:
            print("Database 'waytoo' already exists.")

    except Exception as e:
        print(f"Error during initial database creation check: {e}")
        raise
    finally:
        if cur_root:
            cur_root.close()
        if conn_root:
            conn_root.close()

    conn = None
    cur = None
    try:
        # Connecting to 'waytoo' database for table creation
        conn = get_DB_connection() 
        cur = conn.cursor()

        cur.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'claims'
            );
        """)
        if not cur.fetchone()[0]:
            print("Table 'claims' not found. Creating it...")
            cur.execute(
                """
                CREATE TABLE claims (
                    id SERIAL PRIMARY KEY,
                    customer_id VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    status VARCHAR(50) DEFAULT 'submitted',
                    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    root_cause TEXT,
                    resolution_type TEXT,
                    refund_amount DECIMAL(10, 2),
                    audit_log JSONB DEFAULT '[]'
                );
                """
            )
            conn.commit() 
            print("Table 'claims' created successfully.")
        else:
            print("Table 'claims' already exists.")

        print("Database initialization complete.")
    except Exception as e:
        print(f"Error during table creation: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()