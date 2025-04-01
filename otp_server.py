from flask import Flask, request, jsonify
import smtplib
import random
import time
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()  # Load environment variables from .env file

# Get credentials from environment variables
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Store OTPs with timestamps
otp_storage = {}

def send_otp_email(user_email, otp):
    """Send OTP to user's email"""
    subject = "Your OTP Verification Code"
    body = f"Your OTP code is: {otp}. It is valid for 5 minutes."
    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, user_email, message)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

@app.route("/send-otp", methods=["POST"])
def send_otp():
    """Generate and send OTP"""
    data = request.json
    user_email = data.get("email")

    if not user_email:
        return jsonify({"success": False, "message": "Email is required!"}), 400

    # Prevent multiple OTP requests within 1 minute
    if user_email in otp_storage:
        last_otp_time = otp_storage[user_email]["timestamp"]
        if time.time() - last_otp_time < 60:
            return jsonify({"success": False, "message": "Wait 1 minute before requesting a new OTP!"}), 429

    otp = str(random.randint(100000, 999999))  # Generate a 6-digit OTP
    otp_storage[user_email] = {"otp": otp, "timestamp": time.time()}  # Store OTP with timestamp

    if send_otp_email(user_email, otp):
        return jsonify({"success": True, "message": "OTP sent successfully!"})
    else:
        return jsonify({"success": False, "message": "Failed to send OTP!"}), 500

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    """Verify OTP entered by user"""
    data = request.json
    user_email = data.get("email")
    user_otp = data.get("otp")

    if user_email in otp_storage:
        stored_otp = otp_storage[user_email]["otp"]
        otp_time = otp_storage[user_email]["timestamp"]

        # Check OTP expiry (5 minutes)
        if time.time() - otp_time > 300:
            del otp_storage[user_email]
            return jsonify({"success": False, "message": "OTP expired!"}), 400

        if stored_otp == user_otp:
            del otp_storage[user_email]  # Remove OTP after successful verification
            return jsonify({"success": True, "message": "OTP verified!"})

    return jsonify({"success": False, "message": "Invalid OTP!"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
