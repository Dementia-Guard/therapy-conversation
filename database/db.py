import sqlite3

DB_FILE = "carebot.db"

def get_connection():
    """Establish and return a database connection."""
    return sqlite3.connect(DB_FILE)

def init_db():
    """Initialize the database with the required schema and sample data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create tables
    with open("database/schema.sql", "r") as schema_file:
        cursor.executescript(schema_file.read())

    # Check if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # Insert sample users
        cursor.execute("""
            INSERT INTO users (user_id, full_name, birth_date, hometown)
            VALUES ('1', 'Michael Johnson', '1965-04-10', 'Springfield, Illinois');
        """)
        cursor.execute("""
            INSERT INTO users (user_id, full_name, birth_date, hometown)
            VALUES ('2', 'Sarah Williams', '1970-07-15', 'Austin, Texas');
        """)
        conn.commit()

    conn.close()
