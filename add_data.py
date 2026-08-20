from database import get_db_connection


connection = get_db_connection()
cursor = connection.cursor()


# ---------------- PHARMACY DATA ----------------

pharmacies_data = [
    {
        "name": "City Care Pharmacy",
        "location": "Main Road",
        "medicines": [
            ("paracetamol", 25),
            ("cetirizine", 25),
            ("omeprazole", 25)
        ]
    },
    {
        "name": "Health Plus Pharmacy",
        "location": "Market Street",
        "medicines": [
            ("paracetamol", 30),
            ("ibuprofen", 30)
        ]
    },
    {
        "name": "MedLife Pharmacy",
        "location": "Hospital Road",
        "medicines": [
            ("cetirizine", 28),
            ("omeprazole", 28),
            ("ibuprofen", 28)
        ]
    }
]


for pharmacy_data in pharmacies_data:

    # Add pharmacy
    cursor.execute("""
        INSERT OR IGNORE INTO pharmacies
        (name, location, phone)
        VALUES (?, ?, ?)
    """, (
        pharmacy_data["name"],
        pharmacy_data["location"],
        ""
    ))

    # Get pharmacy ID
    cursor.execute("""
        SELECT id
        FROM pharmacies
        WHERE name = ?
    """, (pharmacy_data["name"],))

    pharmacy = cursor.fetchone()

    if pharmacy:
        pharmacy_id = pharmacy["id"]

        for medicine_name, price in pharmacy_data["medicines"]:

            # Find medicine ID
            cursor.execute("""
                SELECT id
                FROM medicines
                WHERE LOWER(name) = LOWER(?)
            """, (medicine_name,))

            medicine = cursor.fetchone()

            if medicine:
                medicine_id = medicine["id"]

                # Add stock record
                cursor.execute("""
                    INSERT INTO stock
                    (pharmacy_id, medicine_id, available, price)
                    SELECT ?, ?, 1, ?
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM stock
                        WHERE pharmacy_id = ?
                        AND medicine_id = ?
                    )
                """, (
                    pharmacy_id,
                    medicine_id,
                    price,
                    pharmacy_id,
                    medicine_id
                ))


connection.commit()
connection.close()

print("Pharmacies and stock added successfully.")