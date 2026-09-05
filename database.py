import sqlite3
import os

# Always use the database located in the same folder as this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "medmatch.db")


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# CREATE TABLES
# =========================================================

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

    # Add mobile column if old database does not have it
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

    # Add price column if old database does not have it
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

    # ---------------- NOTIFICATIONS ----------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
            REFERENCES users(id)
        )
    """)

    connection.commit()
    connection.close()


# =========================================================
# ADD 19 SAMPLE MEDICINES
# =========================================================

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
        ),

        (
            "Amoxicillin",
            "Antibiotic",
            "An antibiotic used to treat certain bacterial infections.",
            40
        ),

        (
            "Azithromycin",
            "Antibiotic",
            "An antibiotic used for certain bacterial infections.",
            50
        ),

        (
            "Loratadine",
            "Antihistamine",
            "Commonly used to relieve allergy symptoms.",
            30
        ),

        (
            "Pantoprazole",
            "Acid-reducing medicine",
            "Reduces stomach acid production.",
            35
        ),

        (
            "Diclofenac",
            "Pain reliever / anti-inflammatory",
            "Used to reduce pain and inflammation.",
            35
        ),

        (
            "Metformin",
            "Antidiabetic medicine",
            "Used as part of treatment for type 2 diabetes.",
            30
        ),

        (
            "Atorvastatin",
            "Cholesterol-lowering medicine",
            "Used to help lower cholesterol levels.",
            45
        ),

        (
            "Amlodipine",
            "Blood pressure medicine",
            "Used to help manage high blood pressure.",
            25
        ),

        (
            "Losartan",
            "Blood pressure medicine",
            "Used to help manage high blood pressure.",
            35
        ),

        (
            "Montelukast",
            "Respiratory medicine",
            "Used as part of treatment for certain breathing and allergy conditions.",
            40
        ),

        (
            "Salbutamol",
            "Bronchodilator",
            "Helps relax airway muscles and improve airflow.",
            30
        ),

        (
            "Famotidine",
            "Acid-reducing medicine",
            "Reduces the amount of acid produced in the stomach.",
            30
        ),

        (
            "Ondansetron",
            "Anti-nausea medicine",
            "Used to help prevent nausea and vomiting.",
            40
        ),

        (
            "Aspirin",
            "Pain reliever / antiplatelet medicine",
            "Used in certain situations for pain or to reduce platelet clotting under medical guidance.",
            25
        ),

        (
            "Hydrochlorothiazide",
            "Diuretic",
            "Helps the body remove excess salt and water and is used for certain blood pressure conditions.",
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


# =========================================================
# ADD PHARMACIES AND MEDICINE STOCK
# =========================================================

def add_sample_pharmacies_and_stock():

    connection = get_db_connection()
    cursor = connection.cursor()

    # ---------------- PHARMACIES ----------------

    pharmacies_data = [

        (
            "City Care Pharmacy",
            "Main Road",
            "9876543210"
        ),

        (
            "Health Plus Pharmacy",
            "Market Street",
            "9876543211"
        ),

        (
            "MedLife Pharmacy",
            "Hospital Road",
            "9876543212"
        )
    ]

    # Add pharmacies
    for pharmacy in pharmacies_data:

        cursor.execute("""
            SELECT id
            FROM pharmacies
            WHERE name = ?
        """, (pharmacy[0],))

        existing = cursor.fetchone()

        if not existing:

            cursor.execute("""
                INSERT INTO pharmacies
                (name, location, phone)
                VALUES (?, ?, ?)
            """, pharmacy)

    # ---------------- GET PHARMACY IDs ----------------

    cursor.execute("""
        SELECT id, name
        FROM pharmacies
    """)

    pharmacy_rows = cursor.fetchall()

    pharmacy_ids = {
        row["name"]: row["id"]
        for row in pharmacy_rows
    }

    # =====================================================
    # MEDICINE STOCK
    # =====================================================

    stock_data = {

        # ---------------- CITY CARE ----------------

        "City Care Pharmacy": {

            "Paracetamol": 25,
            "Cetirizine": 25,
            "Omeprazole": 25,
            "Amoxicillin": 40,
            "Loratadine": 30,
            "Pantoprazole": 35,
            "Metformin": 30,
            "Amlodipine": 25,
            "Montelukast": 40,
            "Salbutamol": 30,
            "Aspirin": 25
        },

        # ---------------- HEALTH PLUS ----------------

        "Health Plus Pharmacy": {

            "Paracetamol": 30,
            "Ibuprofen": 30,
            "Azithromycin": 50,
            "Diclofenac": 35,
            "Atorvastatin": 45,
            "Losartan": 35,
            "Famotidine": 30,
            "Ondansetron": 40
        },

        # ---------------- MEDLIFE ----------------

        "MedLife Pharmacy": {

            "Cetirizine": 28,
            "Omeprazole": 27,
            "Ibuprofen": 28,
            "Amoxicillin": 42,
            "Pantoprazole": 33,
            "Diclofenac": 36,
            "Metformin": 32,
            "Atorvastatin": 43,
            "Hydrochlorothiazide": 30,
            "Aspirin": 26
        }
    }

    # ---------------- GET MEDICINE IDs ----------------

    cursor.execute("""
        SELECT id, name
        FROM medicines
    """)

    medicine_rows = cursor.fetchall()

    medicine_ids = {
        row["name"]: row["id"]
        for row in medicine_rows
    }

    # ---------------- INSERT STOCK ----------------

    for pharmacy_name, medicine_list in stock_data.items():

        pharmacy_id = pharmacy_ids.get(pharmacy_name)

        if not pharmacy_id:
            continue

        for medicine_name, price in medicine_list.items():

            medicine_id = medicine_ids.get(medicine_name)

            if not medicine_id:
                continue

            # Check whether stock already exists
            cursor.execute("""
                SELECT id
                FROM stock
                WHERE pharmacy_id = ?
                AND medicine_id = ?
            """, (
                pharmacy_id,
                medicine_id
            ))

            existing_stock = cursor.fetchone()

            if existing_stock:

                # Update existing stock
                cursor.execute("""
                    UPDATE stock
                    SET available = 1,
                        price = ?
                    WHERE pharmacy_id = ?
                    AND medicine_id = ?
                """, (
                    price,
                    pharmacy_id,
                    medicine_id
                ))

            else:

                # Add new stock
                cursor.execute("""
                    INSERT INTO stock
                    (
                        pharmacy_id,
                        medicine_id,
                        available,
                        price
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    pharmacy_id,
                    medicine_id,
                    1,
                    price
                ))

    connection.commit()
    connection.close()


# =========================================================
# RUN DATABASE SETUP
# =========================================================

if __name__ == "__main__":

    create_tables()

    add_sample_medicines()

    add_sample_pharmacies_and_stock()

    print("Database setup completed successfully!")