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


# # 🎨 PRO EMAIL DESIGN (As per Screenshots)
def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f1f5f9;font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
        <div style="max-width:550px;margin:20px auto;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.05);border: 1px solid #e2e8f0;">
            
            <div style="background-color:#007bff;padding:40px 20px;text-align:center;color:#ffffff;">
                <h1 style="margin:0;font-size:28px;font-weight:bold;text-transform:uppercase;letter-spacing:1px;">Minhaz Security LTD</h1>
                <p style="margin:5px 0 0;font-size:14px;opacity:0.9;">Your Trusted Security Partner</p>
            </div>

            <div style="padding:30px 25px;">
                <h3 style="color:#007bff;margin:0 0 15px;font-size:18px;">Assalamualikum sir!!</h3>
                <p style="color:#475569;font-size:15px;line-height:1.6;margin:0;">
                    Welcome to our service. Thanks for using our service. We do our best to keep your account secure. ✊
                </p>

                <div style="margin:30px 0;padding:30px;border:1px dashed #007bff;border-radius:10px;text-align:center;background-color:#f8fafc;">
                    <p style="margin:0 0 15px;font-size:13px;color:#64748b;font-weight:bold;text-transform:uppercase;letter-spacing:1px;">
                        YOUR VERIFICATION CODE
                    </p>
                    <div style="font-size:45px;font-weight:800;color:#007bff;letter-spacing:8px;margin-bottom:10px;">
                        {otp}
                    </div>
                    <p style="margin:0;font-size:14px;color:#ef4444;">
                        ⏳ Expiring in 3 minutes
                    </p>
                </div>

                <p style="font-size:13px;color:#64748b;font-style:italic;line-height:1.5;text-align:center;margin-bottom:0;">
                    Please do not share this code with anyone. Our support team will never ask for your OTP.
                </p>
            </div>

            <div style="padding:20px;text-align:center;background-color:#f8fafc;border-top:1px solid #f1f5f9;">
                <p style="margin:0;font-size:12px;color:#94a3b8;">
                    © 2026 Minhaz Security LTD. All rights reserved.
                </p>
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