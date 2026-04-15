import os
import random
import smtplib
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.utils import formataddr
from supabase import create_client

app = Flask(__name__)

# ✅ CORS ENABLE (important)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 🔐 ENV VARIABLES
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_KEY = os.environ.get("API_KEY")

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASS = os.environ.get("SMTP_PASS")

# 🗄️ Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# 🎨 EMAIL DESIGN
def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin:0;padding:0;background:#f4f7f9;font-family:Arial,sans-serif;">

        <div style="max-width:500px;margin:20px auto;background:#ffffff;
        border-radius:15px;overflow:hidden;box-shadow:0 5px 15px rgba(0,0,0,0.1);">

            <div style="background:#1976d2;padding:20px;text-align:center;color:white;">
                <h2 style="margin:0;">Minhaz Security LTD</h2>
                <p style="margin:5px 0 0;font-size:14px;">Your Trusted Security Partner</p>
            </div>

            <div style="padding:25px;">
                
                <h3 style="color:#1976d2;margin-top:0;">Assalamualikum sir!!</h3>

                <p style="color:#555;font-size:15px;">
                    Welcome to our service. We keep your account secure. ✊
                </p>

                <div style="border:1px dashed #90caf9;border-radius:10px;
                padding:20px;text-align:center;margin:25px 0;">

                    <p>YOUR VERIFICATION CODE</p>

                    <div style="font-size:36px;font-weight:bold;
                    letter-spacing:6px;color:#1976d2;">
                        {otp}
                    </div>

                    <p style="color:red;">⏳ Expiring in 3 minutes</p>
                </div>

                <p style="font-size:13px;color:#888;">
                    Do not share this OTP with anyone.
                </p>
            </div>

            <div style="text-align:center;padding:10px;font-size:12px;color:#999;">
                © 2026 Minhaz Security LTD
            </div>

        </div>

    </body>
    </html>
    """


# 📩 SEND EMAIL
def send_email(to_email, otp):
    msg = MIMEText(get_styled_email(otp), "html")

    msg["Subject"] = "OTP Verification"
    msg["From"] = formataddr(("Minhaz Security LTD", SMTP_EMAIL))
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.zoho.com", 587)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASS)
    server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
    server.quit()


# 🔐 SEND OTP
@app.route("/api/send", methods=["GET"])
def send_otp():
    email = request.args.get("email")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    if not email:
        return jsonify({"error": "Email required"}), 400

    otp = str(random.randint(100000, 999999))
    expire = (datetime.utcnow() + timedelta(minutes=3)).isoformat()

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


# 🔐 VERIFY OTP
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

    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    if not email or not user_otp:
        return jsonify({"error": "Missing data"}), 400

    data = supabase.table("otps").select("*").eq("email", email).execute()

    if not data.data:
        return jsonify({"error": "OTP not found"}), 404

    record = data.data[0]
    expire_time = datetime.fromisoformat(record["expire_at"])

    if datetime.utcnow() > expire_time:
        return jsonify({"error": "OTP expired"}), 400

    if record["otp"] == user_otp:
        supabase.table("otps").delete().eq("email", email).execute()
        return jsonify({"status": "Verified"})

    return jsonify({"error": "Invalid OTP"}), 400


# 🌐 HOME
@app.route("/")
def home():
    return "OTP API Running 🚀"


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)