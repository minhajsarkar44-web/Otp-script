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

# 🎨 PREMIUM COMPACT EMAIL DESIGN
def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f1f5f9;font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="max-width:480px;margin:20px auto;background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,0.08);border: 1px solid #e2e8f0;">
            
            <div style="background: linear-gradient(135deg, #007bff, #0056b3); padding:35px 20px; text-align:center; color:#ffffff;">
                <h1 style="margin:0;font-size:26px;font-weight:800;letter-spacing:0.5px;text-transform:uppercase;">Minhaz Security LTD</h1>
                <p style="margin:5px 0 0;font-size:13px;font-weight:300;opacity:0.85;">Your Trusted Security Partner</p>
            </div>

            <div style="padding:30px 25px;">
                <h3 style="color:#1e293b;margin:0 0 10px;font-size:18px;font-weight:700;">Assalamualikum sir!!</h3>
                <p style="color:#475569;font-size:14px;line-height:1.5;margin:0;">
                    Welcome to our service. We prioritize your account's safety. Use the code below to complete your verification. ✊
                </p>

                <div style="margin:25px 0;padding:20px;border:2px solid #f1f5f9;border-radius:12px;text-align:center;background-color:#f8fafc;">
                    <p style="margin:0 0 10px;font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:2px;">
                        VERIFICATION CODE
                    </p>
                    <div style="font-size:42px;font-weight:800;color:#007bff;letter-spacing:12px;line-height:1;">
                        {otp}
                    </div>
                    <p style="margin:12px 0 0;font-size:12px;color:#64748b;display:flex;align-items:center;justify-content:center;gap:4px;">
                        <span style="color:#ef4444;">⌛</span> Valid for 3 minutes only
                    </p>
                </div>

                <p style="font-size:12px;color:#94a3b8;line-height:1.4;text-align:center;margin:0;">
                    Please do not share this code with anyone. Our support team will never ask for your private OTP.
                </p>
            </div>

            <div style="padding:20px;text-align:center;background-color:#ffffff;border-top:1px solid #f1f5f9;">
                <p style="margin:0;font-size:11px;color:#cbd5e1;font-weight:500;">
                    © 2026 MINHAZ SECURITY LTD • SECURE ACCESS
                </p>
            </div>
        </div>
    </body>
    </html>
    """

# 📩 SEND EMAIL
def send_email(to_email, otp):
    html = get_styled_email(otp)
    msg = MIMEText(html, "html")
    msg["Subject"] = f"Code: {otp} | Minhaz Security Verification"
    msg["From"] = f"Minhaz Security <{SMTP_EMAIL}>"
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
        return jsonify({"status": "Success", "message": "OTP sent to email"})
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

    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    if not email or not user_otp:
        return jsonify({"error": "Missing parameters"}), 400

    data = supabase.table("otps").select("*").eq("email", email).execute()
    if not data.data:
        return jsonify({"error": "Record not found"}), 404

    record = data.data[0]
    expire_time = datetime.fromisoformat(record["expire_at"])

    if datetime.utcnow() > expire_time:
        return jsonify({"error": "Code expired"}), 400
    if record["otp"] == user_otp:
        supabase.table("otps").delete().eq("email", email).execute()
        return jsonify({"status": "Verified", "message": "Authentication successful"})

    return jsonify({"error": "Invalid code"}), 400

@app.route("/")
def home():
    return "Minhaz Security API - V2 Premium 🚀"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
