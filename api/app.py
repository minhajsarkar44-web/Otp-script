import os
import random
import smtplib
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from supabase import create_client

app = Flask(__name__)

# 🔐 ENV VARIABLES
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_KEY = os.environ.get("API_KEY")

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASS = os.environ.get("SMTP_PASS")

# 🗄️ Supabase Client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# 📩 Send Email Function
def send_email(to_email, otp):
    msg = MIMEText(f"Your OTP is: {otp} (valid 3 minutes)")
    msg["Subject"] = "OTP Verification"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.zoho.com", 587)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASS)
    server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
    server.quit()


# 🔐 SEND OTP API
@app.route("/api/send", methods=["GET"])
def send_otp():
    email = request.args.get("email")
    key = request.args.get("key")

    # 🔐 API KEY CHECK
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    if not email:
        return jsonify({"error": "Email required"}), 400

    otp = str(random.randint(100000, 999999))
    expire = (datetime.utcnow() + timedelta(minutes=3)).isoformat()

    # 💾 Save OTP in Supabase
    supabase.table("otps").upsert({
        "email": email,
        "otp": otp,
        "expire_at": expire
    }).execute()

    try:
        send_email(email, otp)
        return jsonify({"status": "OTP sent"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔐 VERIFY OTP API
@app.route("/api/verify", methods=["GET", "POST"])
def verify_otp():
    if request.method == "GET":
        email = request.args.get("email")
        user_otp = request.args.get("otp")
        key = request.args.get("key")
    else:
        data = request.json
        email = data.get("email")
        user_otp = data.get("otp")
        key = data.get("key")

    # 🔐 API KEY CHECK
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    if not email or not user_otp:
        return jsonify({"error": "Missing data"}), 400

    data = supabase.table("otps").select("*").eq("email", email).execute()

    if not data.data:
        return jsonify({"error": "OTP not found"}), 404

    record = data.data[0]
    expire_time = datetime.fromisoformat(record["expire_at"])

    # ⏰ Expire check
    if datetime.utcnow() > expire_time:
        return jsonify({"error": "OTP expired"}), 400

    # ✅ Match check
    if record["otp"] == user_otp:
        supabase.table("otps").delete().eq("email", email).execute()
        return jsonify({"status": "Verified"})

    return jsonify({"error": "Invalid OTP"}), 400


# 🌐 Home
@app.route("/")
def home():
    return "OTP API Running"


# 🚀 Run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)