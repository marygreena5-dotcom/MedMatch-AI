import sqlite3
import os

# Always use the database located in the same folder as this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "medmatch.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_db_connection()
    cursor = connection.cursor()

    # ---------------- USERS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            mobile TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(users)")
    columns = [column["name"] for column in cursor.fetchall()]

    if "mobile" not in columns:
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN mobile TEXT
        """)

    # ---------------- MEDICINES ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            purpose TEXT,
            price REAL
        )
    """)

    # ---------------- ALTERNATIVES ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alternatives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            alternative_name TEXT NOT NULL,
            FOREIGN KEY (medicine_id)
            REFERENCES medicines(id)
        )
    """)

    # ---------------- PHARMACIES ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pharmacies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            phone TEXT
        )
    """)

    # ---------------- STOCK ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pharmacy_id INTEGER,
            medicine_id INTEGER,
            available INTEGER DEFAULT 0,
            price REAL,
            FOREIGN KEY (pharmacy_id)
            REFERENCES pharmacies(id),
            FOREIGN KEY (medicine_id)
            REFERENCES medicines(id)
        )
    """)

    cursor.execute("PRAGMA table_info(stock)")
    stock_columns = [column["name"] for column in cursor.fetchall()]

    if "price" not in stock_columns:
        cursor.execute("""
            ALTER TABLE stock
            ADD COLUMN price REAL
        """)

    # ---------------- REMINDERS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            medicine_name TEXT NOT NULL,
            reminder_date TEXT,
            reminder_time TEXT,
            FOREIGN KEY (user_id)
            REFERENCES users(id)
        )
    """)

    # ---------------- ORDERS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            pharmacy_id INTEGER,
            medicine_id INTEGER,
            quantity INTEGER NOT NULL,
            order_date TEXT,
            status TEXT DEFAULT 'Pending',
            FOREIGN KEY (user_id)
            REFERENCES users(id),
            FOREIGN KEY (pharmacy_id)
            REFERENCES pharmacies(id),
            FOREIGN KEY (medicine_id)
            REFERENCES medicines(id)
        )
    """)

    connection.commit()
    connection.close()


def add_sample_medicines():

    connection = get_db_connection()
    cursor = connection.cursor()

    medicines_data = [
        (
            "Paracetamol",
            "Pain reliever / fever reducer",
            "Commonly used to relieve pain and reduce fever.",
            25
        ),
        (
            "Cetirizine",
            "Antihistamine",
            "Commonly used for allergy symptoms.",
            25
        ),
        (
            "Omeprazole",
            "Acid-reducing medicine",
            "Reduces the amount of acid produced in the stomach.",
            25
        ),
        (
            "Ibuprofen",
            "Pain reliever / anti-inflammatory",
            "Used for pain and inflammation.",
            30
        )
    ]

    for medicine in medicines_data:
        cursor.execute("""
            INSERT OR IGNORE INTO medicines
            (name, category, purpose, price)
            VALUES (?, ?, ?, ?)
        """, medicine)

    connection.commit()
    connection.close()