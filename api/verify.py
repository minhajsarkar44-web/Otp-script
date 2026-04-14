from flask import request, jsonify
from datetime import datetime
from core.db import supabase

def handler(request):
    email = request.args.get("email")
    otp = request.args.get("otp")

    data = supabase.table("otps").select("*").eq("email", email).execute()

    if not data.data:
        return jsonify({"error": "not found"}), 404

    record = data.data[0]

    if datetime.utcnow().isoformat() > record["expire_at"]:
        return jsonify({"error": "expired"}), 400

    if record["otp"] == otp:
        supabase.table("otps").delete().eq("email", email).execute()
        return jsonify({"status": "verified"})

    return jsonify({"error": "invalid"}), 400