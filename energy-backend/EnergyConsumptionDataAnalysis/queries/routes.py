from flask import request, jsonify, Blueprint
import os
import re
import resend
from html import escape

query_bp = Blueprint("query", __name__)

# Environment variables
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

# Configure Resend
resend.api_key = RESEND_API_KEY


def send_email(subject, body, to_email):
    """
    Send email using Resend (HTTP-based, non-blocking)
    """
    resend.Emails.send({
        "from": EMAIL_FROM,
        "to": [to_email],
        "subject": subject,
        "html": body.replace("\n", "<br>"),
    })


@query_bp.route("/api/query", methods=["POST"])
def handle_query():
    data = request.get_json(silent=True) or {}

    first_name = data.get("firstName")
    email = data.get("email")
    message = data.get("message")

    if not isinstance(first_name, str) or not isinstance(email, str) or not isinstance(message, str):
        return jsonify({"error": "All fields are required"}), 400
    first_name = first_name.strip()
    email = email.strip()
    message = message.strip()
    if not first_name or len(first_name) > 100 or len(message) > 5000:
        return jsonify({"error": "Name and message must be within the allowed length"}), 400
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 254:
        return jsonify({"error": "Enter a valid email address"}), 400
    if not RESEND_API_KEY or not EMAIL_FROM or not ADMIN_EMAIL:
        return jsonify({"error": "Contact email is not configured"}), 503

    safe_name = escape(first_name)
    safe_email = escape(email)
    safe_message = escape(message)

    try:
        # 1️⃣ Email to admin
        admin_subject = "New Query from Website"
        admin_body = f"""
        <strong>New query received:</strong><br><br>
        <strong>Name:</strong> {safe_name}<br>
        <strong>Email:</strong> {safe_email}<br><br>
        <strong>Message:</strong><br>
        {safe_message}
        """

        send_email(admin_subject, admin_body, ADMIN_EMAIL)

        # 2️⃣ Auto-reply to user
        user_subject = "Thanks for contacting us!"
        user_body = f"""
        Hi {safe_name},<br><br>

        Thank you for reaching out to us.<br>
        We have received your message and will get back to you shortly.<br><br>

        Best regards,<br>
        Smart Energy Monitor Team
        """

        send_email(user_subject, user_body, email)

        return jsonify({
            "success": True,
            "message": "Query submitted successfully"
        }), 200

    except Exception:
        return jsonify({
            "error": "Failed to send email. Please try again later."
        }), 500
