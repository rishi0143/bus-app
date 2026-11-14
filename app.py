
import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "gobus-development-secret")


# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        connection_timeout=10
    )


# Create bookings table
def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            source VARCHAR(100) NOT NULL,
            destination VARCHAR(100) NOT NULL,
            travel_date DATE NOT NULL,
            seats INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    cursor.close()
    connection.close()


# Home page
@app.route("/")
def home():
    bookings = []
    db_error = None

    try:
        init_db()
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM bookings
            ORDER BY id DESC
            LIMIT 5
        """)

        bookings = cursor.fetchall()

        cursor.close()
        connection.close()

    except Error as e:
        db_error = "Unable to connect to the database. Please try again later."
        app.logger.error("Database error: %s", e)

    return render_template(
        "index.html",
        bookings=bookings,
        db_error=db_error,
        today=date.today().isoformat()
    )


# Book ticket
@app.route("/book", methods=["POST"])
def book():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    source = request.form.get("source", "").strip()
    destination = request.form.get("destination", "").strip()
    travel_date = request.form.get("travel_date", "").strip()
    seats = request.form.get("seats", type=int)

    if not all([name, email, phone, source, destination, travel_date]):
        flash("Please fill all the required fields.", "error")
        return redirect(url_for("home"))

    if source.lower() == destination.lower():
        flash("Source and destination cannot be the same.", "error")
        return redirect(url_for("home"))

    if not seats or seats < 1 or seats > 6:
        flash("Please select between 1 and 6 seats.", "error")
        return redirect(url_for("home"))

    try:
        selected_date = date.fromisoformat(travel_date)
        if selected_date < date.today():
            flash("Travel date cannot be in the past.", "error")
            return redirect(url_for("home"))
    except ValueError:
        flash("Please select a valid travel date.", "error")
        return redirect(url_for("home"))

    connection = None
    cursor = None

    try:
        init_db()
        connection = get_db_connection()
        cursor = connection.cursor()

        sql = """
            INSERT INTO bookings
            (name, email, phone, source, destination, travel_date, seats)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            name, email, phone, source,
            destination, travel_date, seats
        )

        cursor.execute(sql, values)
        connection.commit()

        booking_id = cursor.lastrowid

        flash(
            f"Booking successful! Your booking ID is #{booking_id}",
            "success"
        )

    except Error as e:
        if connection:
            connection.rollback()

        app.logger.error("Booking error: %s", e)
        flash("Booking failed. Please check database connection.", "error")

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for("home"))


# Booking history
@app.route("/bookings")
def bookings():
    try:
        init_db()
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM bookings
            ORDER BY id DESC
        """)

        all_bookings = cursor.fetchall()

        cursor.close()
        connection.close()

        return render_template(
            "bookings.html",
            bookings=all_bookings
        )

    except Error as e:
        app.logger.error("Booking history error: %s", e)
        return "Unable to retrieve bookings.", 500


# Health check
@app.route("/health")
def health():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        cursor.close()
        connection.close()

        return {
            "status": "healthy",
            "application": "GoBus",
            "database": "connected"
        }, 200

    except Error as e:
        app.logger.error("Health check failed: %s", e)

        return {
            "status": "unhealthy",
            "database": "disconnected"
        }, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
