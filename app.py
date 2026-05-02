from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from detector import analyze_text, analyze_single_url, analyze_email, analyze_image_file
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_NAME = "safesignal.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mode TEXT,
            risk TEXT,
            score INTEGER,
            input_preview TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_scan(mode, risk, score, input_preview):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scans (mode, risk, score, input_preview, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
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


@app.route("/analyze", methods=["POST"])
def analyze():
    mode = request.form.get("mode") or (request.get_json(silent=True) or {}).get("mode", "text")
    input_preview = ""

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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM scans")
    total_scans = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scans WHERE score >= 15")
    high_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scans WHERE score >= 8 AND score < 15")
    medium_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scans WHERE score < 8")
    low_risk = cursor.fetchone()[0]

    cursor.execute("""
        SELECT mode, risk, score, input_preview, created_at
        FROM scans
        ORDER BY id DESC
        LIMIT 10
    """)
    recent_scans = cursor.fetchall()

    conn.close()

    return jsonify({
        "total_scans": total_scans,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk,
        "reward_balance": 0,
        "recent_scans": [
            {
                "mode": row[0],
                "risk": row[1],
                "score": row[2],
                "input_preview": row[3],
                "created_at": row[4]
            }
            for row in recent_scans
        ]
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )