from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from extensions import bcrypt
from db import get_connection
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors
import re

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    username = str(data.get("email", "")).strip().lower()
    password = data.get("password")

    if not username or not isinstance(password, str):
        return jsonify({"msg": "Email and password are required"}), 400
    if len(username) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", username):
        return jsonify({"msg": "Enter a valid email address"}), 400
    if len(password) < 8 or len(password.encode("utf-8")) > 72:
        return jsonify({"msg": "Password must contain at least 8 characters and at most 72 UTF-8 bytes"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_pw),
        )
        conn.commit()
        return jsonify({"msg": "User created successfully"}), 201

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({"msg": "Username already exists"}), 409

    finally:
        cur.close()
        conn.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("email", "")).strip().lower()
    password = data.get("password")
    if not username or not isinstance(password, str):
        return jsonify({"msg": "Email and password are required"}), 400

    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"msg": "Invalid credentials"}), 401

    token = create_access_token(identity=username)
    return jsonify({"token": token}), 200
