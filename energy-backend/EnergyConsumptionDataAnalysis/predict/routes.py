"""Validated, authenticated energy prediction endpoints."""

import re
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from db import get_connection
from feature_engineering import build_features
from services.documents import extract_document_text

prediction_bp = Blueprint("prediction", __name__)
BASE_DIR = Path(__file__).resolve().parents[1]
artifact = joblib.load(BASE_DIR / "xgb_energy_model (1).pkl")
model = artifact["model"]
FEATURE_COLUMNS = list(artifact["feature_names"])
NUMERIC_FIELDS = {
    "Temperature": (-80, 80),
    "Humidity": (0, 100),
    "SquareFootage": (1, 100_000),
    "Occupancy": (0, 10_000),
    "RenewableEnergy": (0, 1_000_000),
}


def parse_binary(value, name):
    if isinstance(value, bool):
        return int(value)
    normalized = str(value).strip().lower()
    if normalized in {"1", "on", "true", "yes"}:
        return 1
    if normalized in {"0", "off", "false", "no"}:
        return 0
    raise ValueError(f"{name} must be 0/1, on/off, or yes/no")


def parse_input(payload):
    if not isinstance(payload, dict):
        raise ValueError("A JSON object is required")
    current = {}
    for field, (minimum, maximum) in NUMERIC_FIELDS.items():
        try:
            value = float(payload[field])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"{field} must be a number") from None
        if not pd.notna(value) or not minimum <= value <= maximum:
            raise ValueError(f"{field} must be between {minimum} and {maximum}")
        current[field] = value

    for input_name, feature_name in (
        ("HVACUsage", "HVACUsage_1"),
        ("LightingUsage", "LightingUsage_1"),
        ("Holiday", "Holiday_1"),
    ):
        if input_name not in payload:
            raise ValueError(f"{input_name} is required")
        current[feature_name] = parse_binary(payload[input_name], input_name)
    return current


def predict_and_record(connection, username, current, history):
    features = build_features(current, history).reindex(columns=FEATURE_COLUMNS, fill_value=0)
    value = float(model.predict(features)[0])
    if not pd.notna(value):
        raise RuntimeError("The model returned an invalid prediction")
    value = max(0.0, value)
    timestamp = datetime.now(timezone.utc)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO energy_history
                (username, timestamp, temperature, humidity, squarefootage, occupancy,
                 renewableenergy, hvacusage, lightingusage, holiday, energyconsumption)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                username, timestamp, current["Temperature"], current["Humidity"],
                current["SquareFootage"], current["Occupancy"], current["RenewableEnergy"],
                current["HVACUsage_1"], current["LightingUsage_1"], current["Holiday_1"], value,
            ),
        )
    row = {
        "timestamp": timestamp,
        "temperature": current["Temperature"],
        "humidity": current["Humidity"],
        "squarefootage": current["SquareFootage"],
        "occupancy": current["Occupancy"],
        "renewableenergy": current["RenewableEnergy"],
        "hvacusage": current["HVACUsage_1"],
        "lightingusage": current["LightingUsage_1"],
        "holiday": current["Holiday_1"],
        "energyconsumption": value,
    }
    return value, pd.concat([history, pd.DataFrame([row])], ignore_index=True)


def load_user_history(connection, username):
    return pd.read_sql_query(
        "SELECT * FROM energy_history WHERE username = %s ORDER BY timestamp",
        connection,
        params=(username,),
    )


@prediction_bp.post("/predict")
@jwt_required()
def predict():
    try:
        current = parse_input(request.get_json(silent=True))
        username = str(get_jwt_identity())
        with closing(get_connection()) as connection, connection:
            history = load_user_history(connection, username)
            prediction, _ = predict_and_record(connection, username, current, history)
        return jsonify({"predicted_energy": round(prediction, 2)})
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@prediction_bp.post("/predict-from-pdf")
@jwt_required()
def predict_from_pdf():
    upload = request.files.get("file")
    if not upload or not upload.filename or not upload.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Upload a PDF file"}), 400
    try:
        text = extract_document_text(upload.filename, upload.read())
    except Exception:
        return jsonify({"error": "Could not read this PDF"}), 422
    aliases = {
        "Temperature": r"temperature|temp",
        "Humidity": r"humidity|relative humidity",
        "Occupancy": r"occupancy|occupants|residents",
        "SquareFootage": r"square\s*footage|floor\s*area|area",
        "RenewableEnergy": r"renewable\s*energy|solar\s*energy",
    }
    values = {}
    for field, label in aliases.items():
        match = re.search(rf"(?:{label})\s*[:=\-]?\s*(-?\d+(?:\.\d+)?)", text, re.IGNORECASE)
        values[field] = match.group(1) if match else ("0" if field == "RenewableEnergy" else "")
    for field, label in {
        "HVAC": r"hvac(?:\s*usage)?",
        "Lighting": r"lighting(?:\s*usage)?",
        "Holiday": r"holiday",
    }.items():
        match = re.search(
            rf"\b(?:{label})\b\s*[:=\-]?\s*(on|off|yes|no|true|false|1|0)\b",
            text,
            re.IGNORECASE,
        )
        values[field] = parse_binary(match.group(1), field) if match else None
    if not text:
        return jsonify({"error": "No selectable text found in this PDF"}), 422
    return jsonify(values)


@prediction_bp.post("/predict-from-csv")
@jwt_required()
def predict_from_csv():
    upload = request.files.get("file")
    if not upload or not upload.filename or not upload.filename.lower().endswith(".csv"):
        return jsonify({"error": "Upload a CSV file"}), 400
    try:
        frame = pd.read_csv(upload, nrows=1001)
        if len(frame) > 1000:
            return jsonify({"error": "CSV is limited to 1,000 data rows"}), 400
        required = ["Temperature", "Humidity", "SquareFootage", "Occupancy", "RenewableEnergy", "HVAC", "Lighting", "Holiday"]
        missing = [field for field in required if field not in frame.columns]
        if missing:
            return jsonify({"error": f"Missing CSV columns: {', '.join(missing)}"}), 400
        if frame.empty:
            return jsonify({"error": "CSV has no data rows"}), 400
        username = str(get_jwt_identity())
        results = []
        with closing(get_connection()) as connection, connection:
            history = load_user_history(connection, username)
            for _, row in frame.iterrows():
                current = parse_input({
                    "Temperature": row["Temperature"], "Humidity": row["Humidity"],
                    "SquareFootage": row["SquareFootage"], "Occupancy": row["Occupancy"],
                    "RenewableEnergy": row["RenewableEnergy"], "HVACUsage": row["HVAC"],
                    "LightingUsage": row["Lighting"], "Holiday": row["Holiday"],
                })
                prediction, history = predict_and_record(connection, username, current, history)
                results.append({**row.to_dict(), "energyconsumption": round(prediction, 2)})
        return jsonify({"rows": results, "total_rows": len(results)})
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Could not process this CSV"}), 422
