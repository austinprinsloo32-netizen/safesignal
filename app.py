from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from detector import analyze_text, analyze_single_url, analyze_email, analyze_image_file
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")
CORS(app, supports_credentials=True)

DB_NAME = "safesignal.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mode TEXT,
            risk TEXT,
            score INTEGER,
            input_preview TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("PRAGMA table_info(scans)")
    columns = [column[1] for column in cursor.fetchall()]

    if "user_id" not in columns:
        cursor.execute("ALTER TABLE scans ADD COLUMN user_id INTEGER")

    conn.commit()
    conn.close()


def save_scan(user_id, mode, risk, score, input_preview):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scans (user_id, mode, risk, score, input_preview, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        mode,
        risk,
        score,
        str(input_preview)[:150],
        datetime.utcnow().isoformat()
    ))

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    if len(password) < 6:
        return jsonify({"success": False, "message": "Password must be at least 6 characters."}), 400

    password_hash = generate_password_hash(password)

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (email, password_hash, balance, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            email,
            password_hash,
            0,
            datetime.utcnow().isoformat()
        ))

        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        session["user_id"] = user_id
        session["email"] = email

        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "user": {
                "id": user_id,
                "email": email,
                "balance": 0
            }
        })

    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "This email is already registered."}), 409


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    session["user_id"] = user["id"]
    session["email"] = user["email"]

    return jsonify({
        "success": True,
        "message": "Logged in successfully.",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "balance": user["balance"]
        }
    })


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})


@app.route("/me", methods=["GET"])
def me():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"logged_in": False})

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, balance FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        session.clear()
        return jsonify({"logged_in": False})

    return jsonify({
        "logged_in": True,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "balance": user["balance"]
        }
    })


@app.route("/analyze", methods=["POST"])
def analyze():
    mode = request.form.get("mode") or (request.get_json(silent=True) or {}).get("mode", "text")
    input_preview = ""
    user_id = session.get("user_id")

    try:
        if mode == "image":
            image = request.files.get("image")

            if not image:
                return jsonify({
                    "risk": "Invalid Input",
                    "score": 0,
                    "reasons": ["No image was uploaded."],
                    "insights": [],
                    "advice": "Upload a screenshot to analyze."
                }), 400

            input_preview = image.filename or "Screenshot upload"
            result = analyze_image_file(image)

        else:
            data = request.get_json(silent=True) or {}

            if mode == "url":
                url = data.get("url", "")
                input_preview = url
                result = analyze_single_url(url)

            elif mode == "email":
                sender = data.get("sender", "")
                subject = data.get("subject", "")
                body = data.get("body", "")
                input_preview = f"{subject} | {sender} | {body[:80]}"
                result = analyze_email(sender, subject, body)

            else:
                text = data.get("text", "")
                input_preview = text
                result = analyze_text(text)

        save_scan(
            user_id,
            mode,
            result.get("risk", "Unknown"),
            result.get("score", 0),
            input_preview
        )

        return jsonify(result)

    except Exception as e:
        print("Analyze error:", e)
        return jsonify({
            "risk": "Server Error",
            "score": 0,
            "reasons": ["The server could not complete the scan."],
            "insights": [],
            "advice": "Please try again."
        }), 500


@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():
    user_id = session.get("user_id")

    conn = get_db()
    cursor = conn.cursor()

    if user_id:
        filter_sql = "WHERE user_id = ?"
        params = (user_id,)
    else:
        filter_sql = ""
        params = ()

    cursor.execute(f"SELECT COUNT(*) FROM scans {filter_sql}", params)
    total_scans = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM scans {filter_sql} {'AND' if user_id else 'WHERE'} score >= 15", params)
    high_risk = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM scans {filter_sql} {'AND' if user_id else 'WHERE'} score >= 8 AND score < 15", params)
    medium_risk = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM scans {filter_sql} {'AND' if user_id else 'WHERE'} score < 8", params)
    low_risk = cursor.fetchone()[0]

    cursor.execute(f"""
        SELECT mode, risk, score, input_preview, created_at
        FROM scans
        {filter_sql}
        ORDER BY id DESC
        LIMIT 10
    """, params)
    recent_scans = cursor.fetchall()

    balance = 0

    if user_id:
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            balance = user["balance"]

    conn.close()

    return jsonify({
        "logged_in": bool(user_id),
        "total_scans": total_scans,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "reward_balance": balance,
        "recent_scans": [
            {
                "mode": row["mode"],
                "risk": row["risk"],
                "score": row["score"],
                "input_preview": row["input_preview"],
                "created_at": row["created_at"]
            }
            for row in recent_scans
        ]
    })

@app.route("/clear-history", methods=["DELETE"])
def clear_history():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "message": "You must be logged in to clear your history."
        }), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM scans WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Scan history cleared successfully."
    })

    @app.route("/cpx-postback", methods=["GET"])
    def cpx_postback():
        user_id = request.args.get("user_id")
        reward = request.args.get("reward")
        trans_id = request.args.get("trans_id")
        status = request.args.get("status")

    if not user_id or not reward:
        return "missing params", 400

    try:
        conn = get_db()
        cursor = conn.cursor()

        if status == "1":  # approved
            cursor.execute("""
                UPDATE users
                SET balance = balance + ?
                WHERE id = ?
            """, (int(float(reward)), int(user_id)))

        conn.commit()
        conn.close()

        return "ok"

    except Exception as e:
        print("CPX error:", e)
        return "error", 500

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )