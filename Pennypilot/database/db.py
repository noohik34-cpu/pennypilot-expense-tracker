import sqlite3

DATABASE_NAME = "pennypilot.db"


# Connect to database
def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# Create transactions table
def create_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            transaction_date TEXT NOT NULL,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()


# Add a transaction
def add_transaction(
    transaction_type,
    amount,
    category,
    transaction_date,
    description
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions (
            transaction_type,
            amount,
            category,
            transaction_date,
            description
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        transaction_type,
        amount,
        category,
        str(transaction_date),
        description
    ))

    conn.commit()
    conn.close()


# Get all transactions
def get_transactions():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY transaction_date DESC, id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data