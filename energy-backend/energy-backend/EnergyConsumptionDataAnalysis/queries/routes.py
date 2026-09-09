from flask import request, jsonify, Blueprint
import os
import resend
from dotenv import load_dotenv

load_dotenv()

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
    data = request.get_json()

    first_name = data.get("firstName")
    email = data.get("email")
    message = data.get("message")

    if not first_name or not email or not message:
        return jsonify({"error": "All fields are required"}), 400

    try:
        # 1️⃣ Email to admin
        admin_subject = "New Query from Website"
        admin_body = f"""
        <strong>New query received:</strong><br><br>
        <strong>Name:</strong> {first_name}<br>
        <strong>Email:</strong> {email}<br><br>
        <strong>Message:</strong><br>
        {message}
        """

        send_email(admin_subject, admin_body, ADMIN_EMAIL)

        # 2️⃣ Auto-reply to user
        user_subject = "Thanks for contacting us!"
        user_body = f"""
        Hi {first_name},<br><br>

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

    except Exception as e:
        print("Email error:", e)
        return jsonify({
            "error": "Failed to send email. Please try again later."
        }), 500
