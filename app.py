
from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import os
from datetime import date

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)

# ==================================
# DATABASE CONFIGURATION - AWS RDS
# ==================================

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER", "busadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "busbooking")
DB_PORT = int(os.getenv("DB_PORT", "3306"))


def get_db():

    if not DB_HOST or not DB_PASSWORD:
        raise RuntimeError(
            "Please configure DB_HOST and DB_PASSWORD environment variables"
        )

    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        charset="utf8mb4",
        autocommit=False
    )


# ==================================
# DESTINATIONS
# ==================================

destinations = {
    "Hyderabad": {
        "fare": 350,
        "duration": "3 hr 30 min",
        "description": "City of Pearls"
    },

    "Ramappa Temple": {
        "fare": 180,
        "duration": "1 hr 30 min",
        "description": "UNESCO World Heritage Site"
    },

    "Laknavaram Lake": {
        "fare": 220,
        "duration": "1 hr 45 min",
        "description": "Beautiful lake and hanging bridge"
    },

    "Yadadri": {
        "fare": 280,
        "duration": "3 hr",
        "description": "Famous hilltop temple"
    },

    "Bhadrachalam": {
        "fare": 450,
        "duration": "5 hr 30 min",
        "description": "Temple beside Godavari river"
    }
}


# ==================================
# DAILY BUS DEPARTURE TIMES
# ==================================

departures = [
    "06:00 AM",
    "08:30 AM",
    "11:00 AM",
    "02:00 PM",
    "05:30 PM",
    "09:00 PM"
]


# ==================================
# CREATE MYSQL TABLE
# ==================================

def create_table():

    con = get_db()

    try:

        with con.cursor() as cur:

            cur.execute("""
                CREATE TABLE IF NOT EXISTS bookings (

                    id INT AUTO_INCREMENT PRIMARY KEY,

                    name VARCHAR(100) NOT NULL,

                    phone VARCHAR(10) NOT NULL,

                    destination VARCHAR(100) NOT NULL,

                    travel_date DATE NOT NULL,

                    departure VARCHAR(30) NOT NULL,

                    seats INT NOT NULL,

                    total DECIMAL(10,2) NOT NULL,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                )
            """)

        con.commit()

        print("MySQL bookings table created successfully!")

    except Exception:

        con.rollback()
        raise

    finally:

        con.close()


# ==================================
# HOME PAGE
# ==================================

@app.route("/")
def home():

    return render_template(

        "index.html",

        destinations=destinations,

        departures=departures,

        today=date.today().isoformat()

    )


# ==================================
# BOOK BUS TICKET
# ==================================

@app.route("/book", methods=["POST"])
def book():

    name = request.form.get(
        "name", ""
    ).strip()

    phone = request.form.get(
        "phone", ""
    ).strip()

    destination = request.form.get(
        "destination"
    )

    travel_date = request.form.get(
        "travel_date"
    )

    departure = request.form.get(
        "departure"
    )

    try:

        seats = int(
            request.form.get("seats", 0)
        )

    except ValueError:

        seats = 0

    # Validate passenger name

    if not name or len(name) > 100:

        flash("Please enter a valid passenger name.")

        return redirect(url_for("home"))

    # Validate mobile number

    if len(phone) != 10 or not phone.isdigit():

        flash("Enter a valid 10-digit mobile number.")

        return redirect(url_for("home"))

    # Validate destination

    if destination not in destinations:

        flash("Invalid destination.")

        return redirect(url_for("home"))

    # Validate seats

    if seats < 1 or seats > 6:

        flash("Select between 1 and 6 seats.")

        return redirect(url_for("home"))

    # Validate date

    try:

        selected_date = date.fromisoformat(
            travel_date
        )

        if selected_date < date.today():

            flash("Please select today or a future date.")

            return redirect(url_for("home"))

    except (ValueError, TypeError):

        flash("Invalid travel date.")

        return redirect(url_for("home"))

    # Validate departure

    if departure not in departures:

        flash("Invalid departure time.")

        return redirect(url_for("home"))

    # Calculate ticket amount

    fare = destinations[destination]["fare"]

    total = fare * seats

    # Save booking in AWS RDS MySQL

    con = get_db()

    try:

        with con.cursor() as cur:

            cur.execute("""

                INSERT INTO bookings

                (
                    name,
                    phone,
                    destination,
                    travel_date,
                    departure,
                    seats,
                    total
                )

                VALUES (%s, %s, %s, %s, %s, %s, %s)

            """, (

                name,
                phone,
                destination,
                travel_date,
                departure,
                seats,
                total

            ))

            booking_id = cur.lastrowid

        con.commit()

    except Exception:

        con.rollback()

        app.logger.exception("Booking database error")

        flash("Unable to save booking. Please try again.")

        return redirect(url_for("home"))

    finally:

        con.close()

    # Booking confirmation

    return render_template(

        "confirmation.html",

        booking_id=booking_id,

        name=name,

        destination=destination,

        travel_date=travel_date,

        departure=departure,

        seats=seats,

        total=total

    )


# ==================================
# MY BOOKINGS
# ==================================

@app.route("/my-bookings")
def my_bookings():

    phone = request.args.get(
        "phone", ""
    ).strip()

    bookings = []

    if phone:

        if len(phone) != 10 or not phone.isdigit():

            flash("Enter a valid 10-digit mobile number.")

            return redirect(url_for("my_bookings"))

        con = get_db()

        try:

            with con.cursor() as cur:

                cur.execute("""

                    SELECT *

                    FROM bookings

                    WHERE phone = %s

                    ORDER BY id DESC

                """, (phone,))

                bookings = cur.fetchall()

        finally:

            con.close()

    return render_template(

        "my_bookings.html",

        bookings=bookings,

        phone=phone

    )


# ==================================
# DATABASE HEALTH CHECK
# ==================================

@app.route("/health")
def health():

    try:

        con = get_db()

        with con.cursor() as cur:

            cur.execute("SELECT 1")

            result = cur.fetchone()

        con.close()

        return {
            "status": "healthy",
            "database": "connected",
            "result": result
        }, 200

    except Exception:

        app.logger.exception("Database health check failed")

        return {
            "status": "unhealthy",
            "database": "disconnected"
        }, 503


# ==================================
# APPLICATION START
# ==================================

if __name__ == "__main__":

    create_table()

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )
