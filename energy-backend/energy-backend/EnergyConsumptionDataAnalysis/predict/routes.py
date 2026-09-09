from flask import Blueprint, request, jsonify
import joblib
import pandas as pd
from datetime import datetime
from db import get_connection
from feature_engineering import build_features
import os
import uuid
from datetime import timezone

from predict.pdf_utils import extract_text_from_pdf
from predict.llm import extract_features
from predict.normalizer import normalize

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


prediction_bp = Blueprint("prediction", __name__)

saved_obj = joblib.load("xgb_energy_model (1).pkl")
model = saved_obj["model"]
FEATURE_COLUMNS = saved_obj["feature_names"]


@prediction_bp.route("/predict", methods=["POST"])
def predict():
    data = request.json

    current_data = {
        "Temperature": float(data["Temperature"]),
        "Humidity": float(data["Humidity"]),
        "SquareFootage": float(data["SquareFootage"]),
        "Occupancy": float(data["Occupancy"]),
        "RenewableEnergy": float(data["RenewableEnergy"]),
        "HVACUsage_1": int(data["HVACUsage"]),
        "LightingUsage_1": int(data["LightingUsage"]),
        "Holiday_1": int(data["Holiday"])
    }

    conn = get_connection()
    cur = conn.cursor()

    history = pd.read_sql("SELECT * FROM energy_history ORDER BY timestamp", conn)

    X = build_features(current_data, history)
    X = X[FEATURE_COLUMNS]

    prediction = model.predict(X)[0]

    cur.execute("""
        INSERT INTO energy_history
        (timestamp, temperature, humidity, squarefootage, occupancy,
         renewableenergy, hvacusage, lightingusage, holiday, energyconsumption)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        datetime.now(timezone.utc),
        current_data["Temperature"],
        current_data["Humidity"],
        current_data["SquareFootage"],
        current_data["Occupancy"],
        current_data["RenewableEnergy"],
        current_data["HVACUsage_1"],
        current_data["LightingUsage_1"],
        current_data["Holiday_1"],
        float(prediction)
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"predicted_energy": round(float(prediction), 2)})


@prediction_bp.route("/predict-from-pdf", methods=["POST"])
def predict_from_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "PDF only"}), 400

    filename = f"{uuid.uuid4()}.pdf"
    path = os.path.join(UPLOAD_DIR, filename)
    file.save(path)

    try:
        text = extract_text_from_pdf(path)
        llm_data = extract_features(text)
        final_data = normalize(llm_data)

        return jsonify(final_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if os.path.exists(path):
            os.remove(path)


@prediction_bp.route("/predict-from-csv", methods=["POST"])
def predict_from_csv():
    if "file" not in request.files:
        return jsonify({"error": "No CSV file uploaded"}), 400

    file = request.files["file"]

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files allowed"}), 400

    df = pd.read_csv(file)

    REQUIRED_COLUMNS = [
        "Temperature",
        "Humidity",
        "SquareFootage",
        "Occupancy",
        "RenewableEnergy",
        "HVACUsage",
        "LightingUsage",
        "Holiday",
    ]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return jsonify({"error": f"Missing columns: {missing}"}), 400

    conn = get_connection()
    cur = conn.cursor()
    
    history = pd.read_sql(
        "SELECT * FROM energy_history ORDER BY timestamp",
        conn
    )

    results = []

    for _, row in df.iterrows():
        current_data = {
            "Temperature": float(row["Temperature"]),
            "Humidity": float(row["Humidity"]),
            "SquareFootage": float(row["SquareFootage"]),
            "Occupancy": float(row["Occupancy"]),
            "RenewableEnergy": float(row["RenewableEnergy"]),
            "HVACUsage_1": int(row["HVACUsage"]),
            "LightingUsage_1": int(row["LightingUsage"]),
            "Holiday_1": int(row["Holiday"]),
        }

        # 🔹 Build features using UPDATED history
        X = build_features(current_data, history)
        X = X[FEATURE_COLUMNS]

        prediction = float(model.predict(X)[0])

        timestamp = datetime.now(timezone.utc)

        # 🔹 Insert prediction into DB
        cur.execute("""
            INSERT INTO energy_history
            (timestamp, temperature, humidity, squarefootage, occupancy,
             renewableenergy, hvacusage, lightingusage, holiday, energyconsumption)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            timestamp,
            current_data["Temperature"],
            current_data["Humidity"],
            current_data["SquareFootage"],
            current_data["Occupancy"],
            current_data["RenewableEnergy"],
            current_data["HVACUsage_1"],
            current_data["LightingUsage_1"],
            current_data["Holiday_1"],
            prediction
        ))

        # 🔹 Update in-memory history (CRITICAL)
        history = pd.concat([
            history,
            pd.DataFrame([{
                "timestamp": timestamp,
                "temperature": current_data["Temperature"],
                "humidity": current_data["Humidity"],
                "squarefootage": current_data["SquareFootage"],
                "occupancy": current_data["Occupancy"],
                "renewableenergy": current_data["RenewableEnergy"],
                "hvacusage": current_data["HVACUsage_1"],
                "lightingusage": current_data["LightingUsage_1"],
                "holiday": current_data["Holiday_1"],
                "energyconsumption": prediction
            }])
        ], ignore_index=True)


        results.append({
            **row.to_dict(),
            "energyconsumption": round(prediction, 2)
        })
        
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "rows": results,
        "total_rows": len(results)
    })



