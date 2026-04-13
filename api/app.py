import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Zoho SMTP Credentials
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587
SENDER_EMAIL = "dev_minhaz@zohomail.com"
# পাসওয়ার্ডটি আমরা রেন্ডার ড্যাশবোর্ড থেকে সেট করবো (নিরাপত্তার জন্য)
SENDER_PASSWORD = os.environ.get("SMTP_PASSWORD", "3357GAS8KSPr") 

otp_db = {}

def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: sans-serif; background-color: #f4f7f9;">
        <div style="max-width: 450px; margin: 20px auto; background: #fff; border-radius: 15px; overflow: hidden; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
            <div style="background: #007bff; padding: 20px; text-align: center; color: #fff;">
                <h2>Minhaz Security LTD</h2>
            </div>
            <div style="padding: 30px; text-align: center;">
                <p>Your Verification Code:</p>
                <h1 style="font-size: 40px; color: #007bff; letter-spacing: 5px;">{otp}</h1>
                <p style="color: red;">Expires in 3 minutes</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/')
def home():
    return "Minhaz Security LTD - OTP Server is Online!"

@app.route('/api/send')
def send_otp():
    email = request.args.get('email')
    if not email:
        return jsonify({"status": "error", "msg": "Email required"}), 400
    
    otp = str(random.randint(100000, 999999))
    otp_db[email] = {"otp": otp, "expire": datetime.now() + timedelta(minutes=3)}
    
    try:
        msg = MIMEMultipart()
        msg["Message-ID"] = make_msgid(domain='minhaz-security.com')
        msg["Date"] = formatdate(localtime=True)
        msg["From"] = f"Minhaz Security LTD <{SENDER_EMAIL}>"
        msg["To"] = email
        msg["Subject"] = f"OTP: {otp}"
        
        msg.attach(MIMEText(get_styled_email(otp), "html"))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/verify', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        data = request.json
        email = data.get('email') if data else None
        user_otp = data.get('otp') if data else None
    else:
        email = request.args.get('email')
        user_otp = request.args.get('otp')
    
    if email in otp_db:
        record = otp_db[email]
        if datetime.now() < record["expire"] and record["otp"] == user_otp:
            del otp_db[email]
            return jsonify({"status": "ok", "msg": "Verification Successful"})
            
    return jsonify({"status": "error", "msg": "Invalid or Expired OTP"})

if __name__ == "__main__":
    # রেন্ডারের জন্য পোর্ট সেটিংস
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
