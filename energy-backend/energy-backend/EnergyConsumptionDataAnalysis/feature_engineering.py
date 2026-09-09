import pandas as pd
import numpy as np
from datetime import datetime, timezone

def build_features(current, history):
    # ---------- CURRENT TIME (UTC for Supabase) ----------
    now = datetime.now(timezone.utc)

    # ---------- HISTORY DATA ----------
    df = history.copy()

    # Normalize column names to avoid Supabase mismatches
    df.columns = df.columns.str.lower()

     # ---------- HARD SANITIZATION ----------
    if "energyconsumption" in df.columns:
        df["energyconsumption"] = pd.to_numeric(
            df["energyconsumption"], errors="coerce"
        )

    # Drop rows where energy is invalid
    df = df.dropna(subset=["energyconsumption"])

    # ---------- SAFE LAG FUNCTIONS ----------
    def safe_lag(col, lag, default=0):
        if col in df.columns and len(df) > lag:
            val = df.iloc[-lag][col]
            return float(val) if pd.notna(val) else default
        return default

    def safe_roll_mean(col, window, default=0):
        if col in df.columns and len(df) >= window:
            val = df[col].tail(window).mean()
            return float(val) if pd.notna(val) else default
        return default

    def safe_roll_std(col, window, default=0):
        if col in df.columns and len(df) >= window:
            val = df[col].tail(window).std()
            return float(val) if pd.notna(val) else default
        return default

    # ---------- DAY OF WEEK ----------
    dow = now.strftime("%A")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # ---------- FEATURE DICTIONARY ----------
    features = {
        # ----- BASE INPUTS -----
        "Temperature": float(current["Temperature"]),
        "Humidity": float(current["Humidity"]),
        "SquareFootage": float(current["SquareFootage"]),
        "Occupancy": float(current["Occupancy"]),
        "RenewableEnergy": float(current["RenewableEnergy"]),

        # ----- TIME FEATURES -----
        "hour_sin": np.sin(2 * np.pi * now.hour / 24),
        "hour_cos": np.cos(2 * np.pi * now.hour / 24),
        "Temp_Occupancy": float(current["Temperature"]) * float(current["Occupancy"]),

        # ----- LAG FEATURES -----
        "energy_lag_1": safe_lag("energyconsumption", 1),
        "energy_lag_3": safe_lag("energyconsumption", 3),
        "energy_lag_24": safe_lag("energyconsumption", 24),

        # ----- ROLLING FEATURES -----
        "energy_roll_mean_6": safe_roll_mean("energyconsumption", 6),
        "energy_roll_std_6": safe_roll_std("energyconsumption", 6),
        "energy_roll_mean_24": safe_roll_mean("energyconsumption", 24),
        "energy_roll_std_24": safe_roll_std("energyconsumption", 24),

        # ----- BINARY FEATURES -----
        "HVACUsage_1": int(current["HVACUsage_1"]),
        "LightingUsage_1": int(current["LightingUsage_1"]),
        "Holiday_1": int(current["Holiday_1"]),

        # ----- HOUR BINS -----
        "hour_bin_morning": int(6 <= now.hour < 12),
        "hour_bin_afternoon": int(12 <= now.hour < 18),
        "hour_bin_evening": int(18 <= now.hour < 24),
        "hour_bin_night": int(0 <= now.hour < 6),
    }

    # ---------- ONE-HOT DAY OF WEEK ----------
    for d in days:
        features[f"DayOfWeek_{d}"] = 1 if d == dow else 0

    # ---------- FINAL DATAFRAME ----------
    X = pd.DataFrame([features])

    # Force numeric safety
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

    return X

