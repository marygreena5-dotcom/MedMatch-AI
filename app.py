from flask import Flask, render_template, request, redirect, url_for, session
from database import create_tables, get_db_connection, add_sample_medicines
from medicines import medicines
from pharmacies import pharmacies
from difflib import get_close_matches

app = Flask(__name__)
create_tables()
add_sample_medicines()


# Secret key required for Flask sessions
app.secret_key = "medmatch-demo-secret-key"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    message = None

    if request.method == "POST":

        email_or_mobile = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, name, email, mobile
            FROM users
            WHERE (email = ? OR mobile = ?)
            AND password = ?
        """, (
            email_or_mobile,
            email_or_mobile,
            password
        ))

        user = cursor.fetchone()

        connection.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            return redirect(url_for("dashboard"))

        message = "Invalid email/mobile number or password."

    return render_template(
        "login.html",
        message=message
    )


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    message = None

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            message = "Passwords do not match."
            return render_template("register.html", message=message)

        if not name or not email or not mobile or not password:
            message = "Please fill in all fields."
            return render_template("register.html", message=message)

        connection = get_db_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (name, email, password, mobile)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                password,
                mobile
            ))

            connection.commit()
            connection.close()

            return redirect(url_for("login"))

        except Exception:

            connection.close()

            message = "This email may already be registered."

    return render_template(
        "register.html",
        message=message
    )
# ---------------- ADMIN LOGIN ----------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    message = None

    # Demo admin credentials
    ADMIN_EMAIL = "admin@medmatch.com"
    ADMIN_PASSWORD = "admin123"

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:

            session["admin_logged_in"] = True
            session["admin_email"] = email

            return redirect(url_for("admin_orders"))

        message = "Invalid admin email or password."

    return render_template(
        "admin_login.html",
        message=message
    )
    # ---------------- REFILL REMINDER ----------------
@app.route("/reminder", methods=["GET", "POST"])
def reminder():

    user_id = session.get("user_id")

    # User must be logged in
    if not user_id:
        return redirect(url_for("login"))

    message = None

    if request.method == "POST":

        medicine = request.form.get("medicine", "").strip()
        reminder_date = request.form.get("reminder_date", "").strip()

        if not medicine or not reminder_date:
            message = "Please enter medicine name and reminder date."

        else:
            # Save reminder in session for now
            session["reminder"] = {
                "medicine": medicine,
                "date": reminder_date
            }

            message = "Refill reminder saved successfully!"

    return render_template(
        "reminder.html",
        message=message,
        reminder=session.get("reminder")
    )


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("login"))

    reminder = session.get("reminder")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get latest notification for this user
    cursor.execute("""
        SELECT id, message, created_at
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    notification = cursor.fetchone()

    connection.close()

    return render_template(
        "dashboard.html",
        reminder=reminder,
        notification=notification
    )

# ---------------- MEDICINE SEARCH ----------------
@app.route("/search", methods=["GET", "POST"])
def search():
    medicine = None
    result = None
    suggestion = None

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip()

        connection = get_db_connection()
        cursor = connection.cursor()

        # Exact match from SQLite
        cursor.execute("""
            SELECT id, name, category, purpose, price
            FROM medicines
            WHERE LOWER(name) = LOWER(?)
        """, (medicine,))

        row = cursor.fetchone()

        if row:
            result = {
                "name": row["name"],
                "category": row["category"],
                "purpose": row["purpose"],
                "price": row["price"]
            }

            # Get alternatives
            cursor.execute("""
                SELECT alternative_name
                FROM alternatives
                WHERE medicine_id = ?
            """, (row["id"],))

            result["alternatives"] = [
                item["alternative_name"]
                for item in cursor.fetchall()
            ]

        connection.close()

    return render_template(
        "search.html",
        medicine=medicine,
        result=result,
        suggestion=suggestion
    )

# ---------------- AI MEDICINE MATCH ----------------
@app.route("/match", methods=["GET", "POST"])
def match():
    medicine = None
    result = None
    similarity_score = None

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip()

        connection = get_db_connection()
        cursor = connection.cursor()

        # Get all medicine names from SQLite
        cursor.execute("SELECT id, name, category, purpose FROM medicines")
        rows = cursor.fetchall()

        # Create a lookup dictionary
        medicine_names = {
            row["name"].lower(): row
            for row in rows
        }

        search_name = medicine.lower()

        # Find closest medicine name
        matches = get_close_matches(
            search_name,
            medicine_names.keys(),
            n=1,
            cutoff=0.5
        )

        if matches:
            matched_name = matches[0]
            row = medicine_names[matched_name]

            # Calculate similarity percentage
            from difflib import SequenceMatcher

            similarity_score = round(
                SequenceMatcher(
                    None,
                    search_name,
                    matched_name
                ).ratio() * 100,
                2
            )

            result = {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "purpose": row["purpose"]
            }

            # Get alternatives
            cursor.execute("""
                SELECT alternative_name
                FROM alternatives
                WHERE medicine_id = ?
            """, (row["id"],))

            result["alternatives"] = [
                item["alternative_name"]
                for item in cursor.fetchall()
            ]

        connection.close()

    return render_template(
        "match.html",
        medicine=medicine,
        result=result,
        similarity_score=similarity_score
    )
# ---------------- PHARMACY FINDER ----------------
@app.route("/pharmacy", methods=["GET", "POST"])
def pharmacy():
    medicine = None
    results = []

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip()

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                pharmacies.name,
                pharmacies.location,
                stock.price,
                stock.available
            FROM stock
            JOIN pharmacies
                ON stock.pharmacy_id = pharmacies.id
            JOIN medicines
                ON stock.medicine_id = medicines.id
            WHERE LOWER(medicines.name) = LOWER(?)
              AND stock.available = 1
        """, (medicine,))

        rows = cursor.fetchall()

        # Pharmacy details for map and distance
        pharmacy_locations = {
            "City Care Pharmacy": {
                "latitude": 8.1835,
                "longitude": 77.4118
            },

            "Health Plus Pharmacy": {
                "latitude": 8.1815,
                "longitude": 77.4150
            },

            "MedLife Pharmacy": {
                "latitude": 8.1870,
                "longitude": 77.4085
            }
        }

        for row in rows:

            pharmacy_name = row["name"]

            location_data = pharmacy_locations.get(
                pharmacy_name
            )

            if location_data:

                results.append({
                  "name": pharmacy_name,
                  "location": row["location"],
                  "price": f"₹{row['price']:.2f}",
                  "available": row["available"],
                  "latitude": location_data["latitude"],
                  "longitude": location_data["longitude"],

                  "rating": {
                  "City Care Pharmacy": 4.3,
                  "Health Plus Pharmacy": 4.5,
                  "MedLife Pharmacy": 4.2
                  }.get(pharmacy_name, 4.0),

                  "opening_time": {
                  "City Care Pharmacy": "8:00 AM",
                  "Health Plus Pharmacy": "9:00 AM",
                  "MedLife Pharmacy": "8:30 AM"
                  }.get(pharmacy_name, "9:00 AM"),

                  "closing_time": {
                  "City Care Pharmacy": "9:00 PM",
                  "Health Plus Pharmacy": "10:00 PM",
                  "MedLife Pharmacy": "8:30 PM"
                  }.get(pharmacy_name, "9:00 PM")
                })
        connection.close()

    return render_template(
        "pharmacy.html",
        medicine=medicine,
        results=results
    )

# ---------------- PRICE COMPARISON ----------------
@app.route("/price", methods=["GET", "POST"])
def price():
    medicine = None
    results = []
    searched = False

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip()
        searched = True

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                pharmacies.name,
                pharmacies.location,
                stock.price
            FROM stock
            JOIN pharmacies
                ON stock.pharmacy_id = pharmacies.id
            JOIN medicines
                ON stock.medicine_id = medicines.id
            WHERE LOWER(medicines.name) = LOWER(?)
              AND stock.available = 1
            ORDER BY stock.price ASC
        """, (medicine,))

        rows = cursor.fetchall()

        for row in rows:
            results.append({
                "name": row["name"],
                "location": row["location"],
                "price": row["price"]
            })

        connection.close()

    return render_template(
        "price.html",
        medicine=medicine,
        results=results,
        searched=searched
    )
# ---------------- MEDICINE INFORMATION ----------------
@app.route("/medicine-info", methods=["GET", "POST"])
def medicine_info():
    medicine = None
    result = None
    searched = False

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip().lower()
        searched = True

        # Exact medicine search
        if medicine in medicines:
            result = medicines[medicine]

        else:
            # Find closest medicine name
            matches = get_close_matches(
                medicine,
                medicines.keys(),
                n=1,
                cutoff=0.6
            )

            if matches:
                medicine = matches[0]
                result = medicines[matches[0]]

    return render_template(
        "medicine_info.html",
        medicine=medicine,
        result=result,
        searched=searched
    )


# ---------------- MY PROFILE ----------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    connection = get_db_connection()

    user = connection.execute(
        "SELECT id, name, email, mobile FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()

    connection.close()

    return render_template("profile.html", user=user)
# ---------------- ORDER MEDICINE ----------------
@app.route("/order", methods=["GET", "POST"])
def order():

    connection = get_db_connection()
    cursor = connection.cursor()

    message = None
    order_details = None

    # Get all pharmacies
    cursor.execute("""
        SELECT id, name, location
        FROM pharmacies
        ORDER BY name
    """)

    pharmacies = cursor.fetchall()

    # ---------------- PLACE ORDER ----------------
    if request.method == "POST":

        medicine_name = request.form.get("medicine", "").strip()
        pharmacy_id = request.form.get("pharmacy_id")
        quantity = request.form.get("quantity")

        # Check whether user is logged in
        user_id = session.get("user_id")

        if not user_id:
            connection.close()
            return redirect(url_for("login"))

        # Check quantity
        try:
            quantity = int(quantity)

            if quantity < 1:
                raise ValueError

        except (ValueError, TypeError):

            message = "Please enter a valid quantity."

            connection.close()

            return render_template(
                "order.html",
                pharmacies=pharmacies,
                message=message,
                order_details=None
            )

        # Find medicine
        cursor.execute("""
            SELECT id, name
            FROM medicines
            WHERE LOWER(name) = LOWER(?)
        """, (medicine_name,))

        medicine = cursor.fetchone()

        if not medicine:

            message = "Medicine was not found in the database."

            connection.close()

            return render_template(
                "order.html",
                pharmacies=pharmacies,
                message=message,
                order_details=None
            )

        # Check pharmacy stock
        cursor.execute("""
            SELECT
                pharmacies.id,
                pharmacies.name,
                pharmacies.location,
                medicines.id AS medicine_id,
                medicines.name AS medicine_name,
                stock.price,
                stock.available
            FROM stock
            JOIN pharmacies
                ON stock.pharmacy_id = pharmacies.id
            JOIN medicines
                ON stock.medicine_id = medicines.id
            WHERE pharmacies.id = ?
            AND medicines.id = ?
        """, (pharmacy_id, medicine["id"]))

        stock = cursor.fetchone()

        if not stock:

            message = "This medicine is not available at the selected pharmacy."

            connection.close()

            return render_template(
                "order.html",
                pharmacies=pharmacies,
                message=message,
                order_details=None
            )

        if stock["available"] != 1:

            message = "This medicine is currently out of stock."

            connection.close()

            return render_template(
                "order.html",
                pharmacies=pharmacies,
                message=message,
                order_details=None
            )

        # Calculate total price
        price = float(stock["price"] or 0)
        total_price = price * quantity

        # Current date and time
        from datetime import datetime

        order_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save order
        cursor.execute("""
            INSERT INTO orders
            (
                user_id,
                pharmacy_id,
                medicine_id,
                quantity,
                order_date,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            pharmacy_id,
            medicine["id"],
            quantity,
            order_date,
            "Pending"
        ))

        connection.commit()

        order_id = cursor.lastrowid

        # Create notification message
        notification = (
            f"Order #{order_id} placed successfully! "
            f"{medicine['name']} × {quantity} "
            f"from {stock['name']} is now Pending."
        )

        session["notification"] = notification

        # Confirmation information
        order_details = {
            "id": order_id,
            "medicine": stock["medicine_name"],
            "pharmacy": stock["name"],
            "location": stock["location"],
            "quantity": quantity,
            "price": price,
            "total": total_price,
            "status": "Pending"
        }

        message = "Order placed successfully!"

    connection.close()

    return render_template(
        "order.html",
        pharmacies=pharmacies,
        message=message,
        order_details=order_details
    )
    # ---------------- MY ORDERS ----------------
@app.route("/orders")
def orders():

    user_id = session.get("user_id")

    # User must be logged in
    if not user_id:
        return redirect(url_for("login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            orders.id,
            medicines.name AS medicine,
            pharmacies.name AS pharmacy,
            pharmacies.location,
            orders.quantity,
            stock.price,
            orders.order_date,
            orders.status
        FROM orders

        JOIN medicines
            ON orders.medicine_id = medicines.id

        JOIN pharmacies
            ON orders.pharmacy_id = pharmacies.id

        LEFT JOIN stock
            ON stock.medicine_id = orders.medicine_id
            AND stock.pharmacy_id = orders.pharmacy_id

        WHERE orders.user_id = ?

        ORDER BY orders.id DESC
    """, (user_id,))

    orders_data = cursor.fetchall()

    connection.close()

    return render_template(
        "orders.html",
        orders=orders_data
    )
# ---------------- PHARMACY ORDER MANAGEMENT ----------------
@app.route("/admin/orders")
def admin_orders():
        # Admin must be logged in
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            orders.id,
            users.name AS customer,
            medicines.name AS medicine,
            pharmacies.name AS pharmacy,
            pharmacies.location,
            orders.quantity,
            stock.price,
            orders.order_date,
            orders.status
        FROM orders

        JOIN users
            ON orders.user_id = users.id

        JOIN medicines
            ON orders.medicine_id = medicines.id

        JOIN pharmacies
            ON orders.pharmacy_id = pharmacies.id

        LEFT JOIN stock
            ON stock.medicine_id = orders.medicine_id
            AND stock.pharmacy_id = orders.pharmacy_id

        ORDER BY orders.id DESC
    """)

    orders_data = cursor.fetchall()

    connection.close()

    return render_template(
        "admin_orders.html",
        orders=orders_data
    )
# ---------------- UPDATE ORDER STATUS ----------------
@app.route("/admin/update-order", methods=["POST"])
def update_order_status():
        # Admin must be logged in
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    order_id = request.form.get("order_id")
    status = request.form.get("status")

    connection = get_db_connection()
    cursor = connection.cursor()

    # Get order information before updating
    cursor.execute("""
        SELECT
            orders.user_id,
            medicines.name AS medicine,
            pharmacies.name AS pharmacy,
            orders.quantity
        FROM orders
        JOIN medicines
            ON orders.medicine_id = medicines.id
        JOIN pharmacies
            ON orders.pharmacy_id = pharmacies.id
        WHERE orders.id = ?
    """, (order_id,))

    order = cursor.fetchone()

    if order:

        # Update order status
        cursor.execute("""
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """, (status, order_id))

        connection.commit()

        # Create notification for the customer
        notification = (
            f"Order #{order_id}: "
            f"{order['medicine']} × {order['quantity']} "
            f"from {order['pharmacy']} is now {status}."
        )

        # Store notification for that user
        cursor.execute("""
            INSERT INTO notifications
            (user_id, message)
            VALUES (?, ?)
        """, (
            order["user_id"],
            notification
        ))

        connection.commit()

    connection.close()

    return redirect(url_for("admin_orders"))
# ---------------- RUN APPLICATION ----------------
if __name__ == "__main__":
    app.run(debug=True)