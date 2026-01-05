from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import sqlite3
from datetime import datetime
import csv
import jwt
from functools import wraps
import os

DB_NAME = os.path.join(os.path.dirname(__file__), "database.db")


app = Flask(__name__)
CORS(app)

DB_NAME = "database.db"
SECRET_KEY = "supersecret123"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- DB ----------
with get_db() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            created_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dob TEXT,
            age INTEGER,
            gender TEXT,
            place TEXT,
            appointment_date TEXT,
            timing TEXT,
            status TEXT DEFAULT 'New',
            created_at TEXT
        )
    """)

@app.route("/")
def home():
    return "Wellness Appointment API Running"

# ---------- JWT ----------
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token missing"}), 403
        try:
            jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except:
            return jsonify({"error": "Invalid token"}), 403
        return f(*args, **kwargs)
    return decorated

# ---------- USER AUTH ----------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    print("SIGNUP DATA:", data)  
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO users (name, email, password, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                data["name"],
                data["email"],
                data["password"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
        return jsonify({"success": True})
    except:
        return jsonify({"success": False, "message": "User already exists"})

@app.route("/user-login", methods=["POST"])
def user_login():
    data = request.json
    print("LOGIN DATA:", data)
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (data["email"], data["password"])
        ).fetchone()

    if user:
        token = jwt.encode(
            {"user": user["email"], "role": "user"},
            SECRET_KEY,
            algorithm="HS256"
        )
        return jsonify({"token": token, "name": user["name"]})
    return jsonify({"success": False}), 401

# ---------- APPOINTMENTS ----------
@app.route("/book", methods=["POST"])
def book():
    data = request.json
    with get_db() as conn:
        conn.execute("""
            INSERT INTO appointments
            (name, dob, age, gender, place, appointment_date, timing, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'New', ?)
        """, (
            data["name"],
            data["dob"],
            data["age"],
            data["gender"],
            data["place"],
            data["appointment_date"],
            data["timing"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
    return jsonify({"success": True})

# ---------- ADMIN (UNCHANGED) ----------
@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.json
    if data["username"] == "admin" and data["password"] == "admin123":
        token = jwt.encode({"role": "admin"}, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token})
    return jsonify({"success": False}), 401

@app.route("/appointments", methods=["GET"])
@token_required
def appointments():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM appointments ORDER BY id DESC"
        ).fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/delete/<int:appt_id>", methods=["DELETE"])
@token_required
def delete_appointment(appt_id):
    with get_db() as conn:
        conn.execute("DELETE FROM appointments WHERE id=?", (appt_id,))
    return jsonify({"success": True})

@app.route("/status/<int:appt_id>", methods=["PUT"])
@token_required
def update_status(appt_id):
    with get_db() as conn:
        conn.execute(
            "UPDATE appointments SET status='Completed' WHERE id=?",
            (appt_id,)
        )
    return jsonify({"success": True})

@app.route("/export", methods=["GET"])
@token_required
def export_csv():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM appointments").fetchall()

    def generate():
        if rows:
            yield ",".join(rows[0].keys()) + "\n"
            for row in rows:
                yield ",".join([str(row[k]) for k in row.keys()]) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=appointments.csv"}
    )
    
with get_db() as conn:
    print(
        conn.execute(
            "PRAGMA table_info(appointments)"
        ).fetchall()
    )


if __name__ == "__main__":
    app.run(debug=True)
