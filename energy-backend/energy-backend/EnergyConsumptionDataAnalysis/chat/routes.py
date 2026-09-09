from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from chatbot import chat_with_bot

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    messages = request.json["messages"]
    reply = chat_with_bot(messages)
    return jsonify({"reply": reply})
