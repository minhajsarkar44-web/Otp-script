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

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🌐 CORS FIX (IMPORTANT)
def add_cors(res):
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    res.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return res

# Gmail sender design

def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f1f5f9;font-family: 'Segoe UI', Arial, sans-serif;">
        <div style="max-width:450px;margin:20px auto;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 8px 20px rgba(0,0,0,0.05);border: 1px solid #e2e8f0;">
            
            <div style="background-color:#007bff; padding:25px 20px; text-align:center; color:#ffffff;">
                <h1 style="margin:0;font-size:24px;font-weight:bold;letter-spacing:0.5px;text-transform:uppercase;">Minhaz Security LTD</h1>
                <p style="margin:4px 0 0;font-size:12px;opacity:0.9;">Your Trusted Security Partner</p>
            </div>

            <div style="padding:25px 20px; text-align:left;">
                <h3 style="color:#007bff;margin:0 0 10px;font-size:17px;font-weight:700;">Assalamualikum sir!!</h3>
                <p style="color:#475569;font-size:14px;line-height:1.5;margin:0;">
                    Welcome to our service. Thanks for using our service. We do our best to keep your account secure. ✊
                </p>

                <div style="margin:25px 0; padding:20px; border:2px dashed #007bff; border-radius:12px; text-align:center; background-color:#fcfdfe;">
                    <p style="margin:0 0 10px; font-size:12px; color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:1px;">
                        YOUR VERIFICATION CODE
                    </p>
                    
                    <div style="font-size:40px; font-weight:800; color:#007bff; letter-spacing:10px; line-height:1.2; display:block;">
                        {otp}
                    </div>
                    
                    <div style="margin-top:10px; font-size:12px; color:#ef4444; text-align:center;">
                        ⏳ Expiring in 3 minutes
                    </div>
                </div>

                <p style="font-size:11px; color:#94a3b8; line-height:1.5; text-align:center; margin-top:15px; padding: 0 10px;">
                    Please do not share this code with anyone. Our support team will never ask for your private OTP.
                </p>
            </div>

            <div style="padding:15px; text-align:center; background-color:#f8fafc; border-top:1px solid #f1f5f9;">
                <p style="margin:0; font-size:10px; color:#cbd5e1; font-weight:600;">
                    © 2026 MINHAZ SECURITY LTD | Cumilla , Bangladesh
                </p>
            </div>
        </div>
    </body>
    </html>
    """


# 📩 SEND EMAIL
def send_email(to_email, otp):
    msg = MIMEText(get_styled_email(otp), "html")
    msg["Subject"] = "Your OTP Code"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.zoho.com", 587)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASS)
    server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
    server.quit()


# 📩 SEND EMAIL
def send_email(to_email, otp):
    html = get_styled_email(otp)
    msg = MIMEText(html, "html")
    msg["Subject"] = f"Verification Code: {otp}"
    msg["From"] = f"Minhaz Security LTD <{SMTP_EMAIL}>"
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.zoho.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASS)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error: {e}")
        raise


# 🔐 VERIFY OTP
@app.route("/api/verify", methods=["GET", "POST", "OPTIONS"])
def verify_otp():
    if request.method == "OPTIONS":
        return add_cors(jsonify({}))

    data = request.json if request.method == "POST" else request.args

    email = data.get("email")
    user_otp = data.get("otp")
    key = data.get("key")

    if key != API_KEY:
        return add_cors(jsonify({"error": "Unauthorized"})), 401

    result = supabase.table("otps").select("*").eq("email", email).execute()

    if not result.data:
        return add_cors(jsonify({"error": "Not found"})), 404

    record = result.data[0]

    if datetime.utcnow() > datetime.fromisoformat(record["expire_at"]):
        return add_cors(jsonify({"error": "OTP expired"})), 400

    if record["otp"] == user_otp:
        supabase.table("otps").delete().eq("email", email).execute()
        return add_cors(jsonify({"status": "verified"}))

    return add_cors(jsonify({"error": "Invalid OTP"})), 400


# 🏠 HOME
@app.route("/")
def home():
    return "OTP API is running 🚀"


# Vercel handler
def handler(event, context):
    return app(event, context)


if __name__ == "__main__":
    app.run()