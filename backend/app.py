import os
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import pymysql
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message

app = Flask(__name__)
CORS(app)

# ---------------- CONFIGURATION ----------------
# Repo: https://github.com/CloudTechDevOps/aws-ecommerce-otp-authentication.git
# Region: ap-south-1 (Mumbai) — Free Tier (No RDS Proxy)
# Update "host" with your RDS endpoint from: AWS Console → RDS → Databases → Connectivity

db_config = {
    "host": "ecommerce-db-primary",  # <-- Get from AWS Console → RDS → Databases → Connectivity
    "user": "admin",                  # <-- Your RDS master username
    "password": "Cloud123",  # <-- Your RDS master password
    "database": "ecommerce-db-primary"               # <-- Matches DB name in test.sql
}

# GMAIL CONFIG — Use a Google App Password (NOT your Gmail login password)
# Generate at: https://myaccount.google.com/apppasswords
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='vvardhan2211@gmail.com',  # <-- Your Gmail address
    MAIL_PASSWORD='czvk tjjz kiea qrbu'      # <-- Your 16-char Google App Password
)
mail = Mail(app)

# Temp in-memory storage for registrations awaiting OTP verification
pending_users = {}


def get_db_connection():
    return pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/api/health', methods=['GET'])
def health_check():
    # ALB calls this every 30 seconds to verify the app is running
    return jsonify({'status': 'healthy'}), 200
# ---------------- HEALTH CHECK ----------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "region": "ap-south-1"}), 200


# ---------------- SIGNUP LOGIC (2 STEPS) ----------------

@app.route("/api/signup/request", methods=["POST"])
def signup_request():
    data = request.get_json()
    email = data.get("email")
    username = data.get("username")

    otp = str(random.randint(100000, 999999))

    pending_users[email] = {
        "username": username,
        "password": generate_password_hash(data.get("password")),
        "otp": otp,
        "expiry": datetime.now() + timedelta(minutes=10)
    }

    try:
        msg = Message(
            "Google Store - Verify Registration",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Hello {username}, your registration OTP is {otp}. It expires in 10 minutes."
        mail.send(msg)
        return jsonify({"message": "OTP sent to email!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/signup/verify", methods=["POST"])
def signup_verify():
    data = request.get_json()
    email = data.get("email")
    user_otp = data.get("otp")

    user = pending_users.get(email)
    if user and user['otp'] == user_otp and datetime.now() < user['expiry']:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user['username'], email, user['password']))
            conn.commit()
            del pending_users[email]
            return jsonify({"message": "Account created successfully!"}), 201
        except Exception as e:
            return jsonify({"error": "User already exists"}), 400
    return jsonify({"error": "Invalid or expired OTP"}), 401


# ---------------- LOGIN LOGIC (2 STEPS) ----------------

@app.route("/api/login/request", methods=["POST"])
def login_request():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user and check_password_hash(user["password"], password):
        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=5)

        cursor.execute(
            "UPDATE users SET otp_code = %s, otp_expiry = %s WHERE email = %s",
            (otp, expiry, email)
        )
        conn.commit()

        msg = Message(
            "Google Store - Login OTP",
            sender=app.config['MAIL_USERNAME'],
            recipients=[email]
        )
        msg.body = f"Your login OTP is {otp}. It expires in 5 minutes."
        mail.send(msg)

        return jsonify({"message": "OTP sent to email"}), 200

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/api/login/verify", methods=["POST"])
def login_verify():
    data = request.get_json()
    email = data.get("email")
    user_otp = data.get("otp")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = %s AND otp_code = %s",
        (email, user_otp)
    )
    user = cursor.fetchone()

    if user and datetime.now() < user["otp_expiry"]:
        return jsonify({
            "message": "Login successful",
            "user": {"username": user["username"], "email": user["email"]}
        }), 200

    return jsonify({"error": "Invalid or expired OTP"}), 401


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

