import os
import random
import smtplib
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from supabase import create_client

app = Flask(__name__)

# 🔐 ENV VARIABLES
# এই ভেরিয়েবলগুলো আপনার এনভায়রনমেন্টে সেট থাকতে হবে।
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
API_KEY = os.environ.get("API_KEY")

SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_PASS = os.environ.get("SMTP_PASS")

# 🗄️ Supabase Client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 🎨 REFINED COMPACT EMAIL DESIGN
# এই HTML টেমপ্লেটটি আপনার স্ক্রিনশট অনুযায়ী তৈরি এবং রিফাইন করা হয়েছে।
def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f1f5f9;font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
        <div style="max-width:460px;margin:20px auto;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 8px 25px rgba(0,0,0,0.06);border: 1px solid #e2e8f0;">
            
            <div style="background-color:#007bff; padding:25px 20px; text-align:center; color:#ffffff;">
                <h1 style="margin:0;font-size:24px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase;">Minhaz Security LTD</h1>
                <p style="margin:4px 0 0;font-size:12px;font-weight:400;opacity:0.85;">Your Trusted Security Partner</p>
            </div>

            <div style="padding:25px 20px;">
                <h3 style="color:#1e293b;margin:0 0 10px;font-size:16px;font-weight:700;">Assalamualikum sir!!</h3>
                <p style="color:#475569;font-size:13px;line-height:1.5;margin:0;">
                    Welcome to our service. For security reasons, please use the verification code provided below to complete your access. ✊
                </p>

                <div style="margin:20px 0;padding:15px;border:1.5px dashed #007bff;border-radius:10px;text-align:center;background-color:#fcfdfe;">
                    <p style="margin:0 0 8px;font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;">
                        YOUR VERIFICATION CODE
                    </p>
                    
                    <div style="font-size:36px;font-weight:800;color:#007bff;letter-spacing:8px;line-height:1;margin-bottom:8px;word-break:keep-all;">
                        {otp}
                    </div>
                    
                    <p style="margin:0;font-size:11px;color:#ef4444;display:inline-flex;align-items:center;vertical-align:middle;gap:3px;">
                        <span>⏳ Valid for 3 minutes</span>
                    </p>
                </div>

                <p style="font-size:11px;color:#94a3b8;line-height:1.4;text-align:center;margin:0;">
                    Please do not share this code with anyone for your account's security.
                </p>
            </div>

            <div style="padding:15px;text-align:center;background-color:#f8fafc;border-top:1px solid #f1f5f9;">
                <p style="margin:0;font-size:10px;color:#cbd5e1;font-weight:500;">
                    © 2026 MINHAZ SECURITY LTD | Gaza, Palestine
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
    # সাবজেক্ট আপনার ছবির মতো রাখা হয়েছে
    msg["Subject"] = f"Verification Code: {otp}"
    msg["From"] = f"Minhaz Security <{SMTP_EMAIL}>"
    msg["To"] = to_email

    try:
        server = smtplib.SMTP("smtp.zoho.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASS)
        server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Error sending email: {e}")
        raise

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
        return jsonify({"status": "Success", "message": "OTP sent successfully to email", "email": email})
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
        return jsonify({"error": "Missing parameters (email or otp)"}), 400

    try:
        data = supabase.table("otps").select("*").eq("email", email).execute()
        if not data.data:
            return jsonify({"error": "Verification record not found"}), 404

        record = data.data[0]
        expire_time = datetime.fromisoformat(record["expire_at"])

        if datetime.utcnow() > expire_time:
            supabase.table("otps").delete().eq("email", email).execute() #Expired, so clean up
            return jsonify({"error": "Verification code has expired"}), 400
        
        if record["otp"] == user_otp:
            supabase.table("otps").delete().eq("email", email).execute() #Success, clean up
            return jsonify({"status": "Verified", "message": "Verification successful"})
        else:
            return jsonify({"error": "Invalid verification code"}), 400
            
    except Exception as e:
         return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/")
def home():
    return "Minhaz Security OTP API -🚀"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
