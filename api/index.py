import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Zoho SMTP Credentials
SMTP_SERVER = "smtp.zoho.com"
SMTP_PORT = 587
SENDER_EMAIL = "dev_minhaz@zohomail.com"
SENDER_PASSWORD = "3357GAS8KSPr"

# ওটিপি স্টোরেজ
otp_db = {}

def get_styled_email(otp):
    return f"""
    <html>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f9;">
        <table width="100%" bgcolor="#f4f7f9" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center" style="padding: 20px 0;">
                    <table width="450" bgcolor="#ffffff" style="border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); overflow: hidden;">
                        <tr>
                            <td bgcolor="#007bff" style="padding: 30px; text-align: center; color: #ffffff;">
                                <h1 style="margin: 0; font-size: 28px; font-weight: 600;">Security Cloud</h1>
                                <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 14px;">Your Trusted Security Partner</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 40px 30px; color: #333333; line-height: 1.6;">
                                <h3 style="margin-top: 0; color: #007bff;">Assalamualikum sir!!</h3>
                                <p style="font-size: 15px;">Welcome to our service. Thanks for using our service. We do our best to keep your account secure. ✊</p>
                                
                                <p style="font-size: 14px; background: #fff8e1; border-left: 4px solid #ffc107; padding: 10px;">
                                    <strong>Security Notice:</strong> To complete your verification, please use the following one-time password (OTP).
                                </p>

                                <div style="margin: 30px 0; text-align: center; background: #f8f9fa; padding: 30px; border-radius: 12px; border: 1px dashed #007bff;">
                                    <p style="margin: 0 0 10px 0; font-size: 12px; color: #666666; font-weight: bold; letter-spacing: 1px;">YOUR VERIFICATION CODE</p>
                                    <h2 style="margin: 0; font-size: 42px; color: #007bff; letter-spacing: 8px;">{otp}</h2>
                                    <p style="margin: 10px 0 0 0; font-size: 12px; color: #dc3545; font-weight: 500;">⌛ Expiring in 3 minutes</p>
                                </div>

                                <p style="font-size: 13px; color: #666666;">
                                    Please do not share this code with anyone. Our support team will never ask for your OTP. 
                                    If you did not request this code, please ignore this message or contact our support team immediately.
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px; text-align: center; background: #fdfdfd; border-top: 1px solid #eeeeee;">
                                <p style="margin: 0; font-size: 11px; color: #999999;">
                                    &copy; 2026 Security Cloud Inc. All rights reserved.<br>
                                    Powered by Minhaz Security Server
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

@app.route('/')
def home():
    return "Security Cloud OTP Server is Online!"

@app.route('/api/send')
def send_otp():
    email = request.args.get('email')
    if not email:
        return jsonify({"status": "error", "msg": "Email required"}), 400
    
    otp = str(random.randint(100000, 999999))
    otp_db[email] = {"otp": otp, "expire": datetime.now() + timedelta(minutes=3)}
    
    try:
        msg = MIMEMultipart()
        msg["From"] = f"Security Cloud <{SENDER_EMAIL}>"
        msg["To"] = email
        msg["Subject"] = f"Your Verification Code: {otp}"
        msg.attach(MIMEText(get_styled_email(otp), "html"))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/verify', methods=['POST'])
def verify_otp():
    data = request.json
    email = data.get('email')
    user_otp = data.get('otp')
    
    if email in otp_db:
        record = otp_db[email]
        if datetime.now() < record["expire"] and record["otp"] == user_otp:
            del otp_db[email]
            return jsonify({"status": "ok"})
    return jsonify({"status": "error", "msg": "Invalid or Expired OTP"})

if __name__ == "__main__":
    app.run(debug=True)
