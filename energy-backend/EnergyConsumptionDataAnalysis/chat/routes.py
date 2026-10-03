"""Authenticated energy assistant endpoint."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from services.assistant import answer_question

chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/chat")
@jwt_required()
def chat():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected a JSON object"}), 400
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "messages must be a non-empty array"}), 400
    last_message = messages[-1]
    if not isinstance(last_message, dict) or last_message.get("role") != "user" or not isinstance(last_message.get("content"), str):
        return jsonify({"error": "The last message must be from the user"}), 400
    if len(last_message["content"]) > 1000:
        return jsonify({"error": "Keep your question under 1,000 characters"}), 400
    conversation = [
        {"role": item["role"], "content": item["content"].strip()[:1000]}
        for item in messages[-12:]
        if isinstance(item, dict)
        and item.get("role") in {"user", "assistant"}
        and isinstance(item.get("content"), str)
        and item["content"].strip()
    ]
    if not conversation or conversation[-1]["role"] != "user":
        return jsonify({"error": "The last message must be from the user"}), 400
    return jsonify(answer_question(str(get_jwt_identity()), conversation))
