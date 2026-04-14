import random
from flask import request, jsonify
from core.db import supabase
from datetime import datetime, timedelta

def handler(request):
    email = request.args.get("email")
    key = request.args.get("key")

    if not email:
        return jsonify({"error": "email required"}), 400

    otp = str(random.randint(100000, 999999))
    expire = (datetime.utcnow() + timedelta(minutes=3)).isoformat()

    supabase.table("otps").upsert({
        "email": email,
        "otp": otp,
        "expire_at": expire
    }).execute()

    return jsonify({"status": "otp_sent"})