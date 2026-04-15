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


# 🎨 PRO EMAIL DESIGN
def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin:0;padding:0;background:#0f172a;font-family:Arial,sans-serif;">
        
        <div style="max-width:500px;margin:40px auto;background:#111827;
        border-radius:16px;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,0.5);">
            
            <!-- Header -->
            <div style="padding:20px;background:#1f2937;color:white;
            display:flex;align-items:center;">
                
                <div style="width:45px;height:45px;background:#2563eb;
                border-radius:50%;display:flex;align-items:center;justify-content:center;
                font-size:20px;">
                    🔐
                </div>

                <div style="margin-left:12px;">
                    <div style="font-size:16px;font-weight:bold;">Minhaz Security</div>
                    <div style="font-size:12px;color:#9ca3af;">Secure Notification</div>
                </div>
            </div>

            <!-- Body -->
            <div style="padding:25px;">
                
                <div style="background:#1f2937;padding:20px;
                border-radius:12px;color:white;">
                    
                    <p style="margin:0;font-size:14px;color:#d1d5db;">
                        Your verification code:
                    </p>

                    <div style="font-size:38px;font-weight:bold;
                    letter-spacing:6px;color:#22c55e;margin:15px 0;text-align:center;">
                        {otp}
                    </div>

                    <p style="margin:0;font-size:13px;color:#f87171;text-align:center;">
                        ⏳ Valid for 3 minutes
                    </p>
                </div>

                <p style="margin-top:20px;font-size:12px;color:#9ca3af;text-align:center;">
                    If this wasn’t you, ignore this message.
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
    msg["Subject"] = "🔐 OTP Verification"
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

    # 🔒 API KEY CHECK
    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    if not email:
        return jsonify({"error": "Email required"}), 400

    otp = str(random.randint(100000, 999999))
    expire = (datetime.utcnow() + timedelta(minutes=3)).isoformat()

    # 💾 Save OTP
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

    # 🔒 API KEY CHECK
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

    # ✅ Match
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