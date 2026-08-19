from flask import Flask, render_template, request, redirect, url_for, session
from medicines import medicines
from pharmacies import pharmacies
from difflib import get_close_matches

app = Flask(__name__)

# Secret key required for Flask sessions
app.secret_key = "medmatch-demo-secret-key"


# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Simple demo login
        if email and password:
            return redirect(url_for("dashboard"))

    return render_template("login.html")


# ---------------- REGISTER ----------------
@app.route("/register")
def register():
    return render_template("register.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    reminder = session.get("reminder")

    return render_template(
        "dashboard.html",
        reminder=reminder
    )


# ---------------- MEDICINE SEARCH ----------------
@app.route("/search", methods=["GET", "POST"])
def search():
    medicine = None
    result = None
    suggestion = None

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip().lower()

        # Exact match
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
                suggestion = matches[0]
                result = medicines[suggestion]

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

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip().lower()

        if medicine in medicines:
            result = medicines[medicine]

    return render_template(
        "match.html",
        medicine=medicine,
        result=result
    )


# ---------------- PHARMACY FINDER ----------------
@app.route("/pharmacy", methods=["GET", "POST"])
def pharmacy():
    medicine = None
    results = []

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip().lower()

        for pharmacy in pharmacies:
            if medicine in pharmacy["medicines"]:
                results.append(pharmacy)

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
        medicine = request.form.get("medicine", "").strip().lower()
        searched = True

        for pharmacy in pharmacies:
            if medicine in pharmacy["medicines"]:
                results.append(pharmacy)

        # Sort pharmacies from lowest price to highest price
        results.sort(key=lambda x: x["price"])

    return render_template(
        "price.html",
        medicine=medicine,
        results=results,
        searched=searched
    )


# ---------------- REFILL REMINDER ----------------
@app.route("/reminder", methods=["GET", "POST"])
def reminder():
    medicine = None
    date = None
    reminder_set = False

    if request.method == "POST":
        medicine = request.form.get("medicine", "").strip()
        date = request.form.get("date", "").strip()

        if medicine and date:

            # Save reminder in session
            session["reminder"] = {
                "medicine": medicine,
                "date": date
            }

            reminder_set = True

    return render_template(
        "reminder.html",
        medicine=medicine,
        date=date,
        reminder_set=reminder_set
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
    return render_template("profile.html")


# ---------------- RUN APPLICATION ----------------
if __name__ == "__main__":
    app.run(debug=True)