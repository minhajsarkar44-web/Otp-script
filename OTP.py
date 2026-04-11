import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Zoho Credentials
SMTP_SERVER, SMTP_PORT = "smtp.zoho.com", 587
SENDER_EMAIL = "dev_minhaz@zohomail.com"
SENDER_PASSWORD = "3357GAS8KSPr"

otp_db = {}

def get_styled_email(otp):
    return f"""
    <html>
    <body style="font-family: Arial; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 400px; margin: auto; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <div style="background: #007bff; color: #fff; padding: 20px; text-align: center;">
                <h2>Security Cloud</h2>
            </div>
            <div style="padding: 30px; text-align: center;">
                <p>Assalamualikum sir!! Welcome ✊</p>
                <div style="margin: 20px 0; padding: 20px; border: 2px dashed #007bff; border-radius: 10px;">
                    <span style="font-size: 12px; color: #666;">YOUR CODE</span><br>
                    <b style="font-size: 36px; color: #007bff; letter-spacing: 5px;">{otp}</b>
                </div>
                <p style="color: #ff0000; font-size: 12px;">Expire in 3 minutes</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/')
def home(): return "OTP Server is Running!"

@app.route('/api/send')
def send_otp():
    email = request.args.get('email')
    if not email: return jsonify({"status": "error"}), 400
    otp = str(random.randint(100000, 999999))
    otp_db[email] = {"otp": otp, "expire": datetime.now() + timedelta(minutes=3)}
    
    try:
        msg = MIMEMultipart()
        msg["From"] = f"Minhaz Security <{SENDER_EMAIL}>"
        msg["To"] = email
        msg["Subject"] = f"{otp} is your code"
        msg.attach(MIMEText(get_styled_email(otp), "html"))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return jsonify({"status": "ok"})
    except: return jsonify({"status": "error"}), 500

@app.route('/api/verify', methods=['POST'])
def verify_otp():
    data = request.json
    email, user_otp = data.get('email'), data.get('otp')
    if email in otp_db:
        if datetime.now() < otp_db[email]["expire"] and otp_db[email]["otp"] == user_otp:
            del otp_db[email]
            return jsonify({"status": "ok"})
    return jsonify({"status": "error", "msg": "Invalid OTP"})
