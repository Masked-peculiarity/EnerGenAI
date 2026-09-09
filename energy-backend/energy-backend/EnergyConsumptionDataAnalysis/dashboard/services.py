import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    return psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require",
        cursor_factory=RealDictCursor
    )


def get_dashboard_data():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # ---------- KPI CARDS (LAST 7 DAYS) ----------
    cur.execute("""
        SELECT
            AVG(energyconsumption) AS avg_energy,
            MAX(energyconsumption) AS max_energy,
            MIN(energyconsumption) AS min_energy,
            CASE
                WHEN SUM(energyconsumption) > 0
                THEN (SUM(renewableenergy) / SUM(energyconsumption)) * 100
                ELSE 0
            END AS renewable_share
        FROM energy_history
        WHERE timestamp >= NOW() - INTERVAL '7 days'
    """)
    kpi = cur.fetchone() or {}

    # ---------- DAILY CONSUMPTION ----------
    cur.execute("""
        SELECT
            EXTRACT(DOW FROM timestamp) AS day_idx,
            AVG(energyconsumption) AS avg_energy
        FROM energy_history
        GROUP BY day_idx
        ORDER BY day_idx
    """)
    daily_rows = cur.fetchall()

    day_map = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    daily_consumption = [
        {
            "day": day_map[int(row["day_idx"])],
            "value": round(row["avg_energy"], 2)
        }
        for row in daily_rows
    ]

    # ---------- HOURLY PROFILE ----------
    cur.execute("""
        SELECT
            EXTRACT(HOUR FROM timestamp) AS hour,
            AVG(energyconsumption) AS avg_energy
        FROM energy_history
        GROUP BY hour
        ORDER BY hour
    """)
    hourly_profile = [
        {
            "hour": int(row["hour"]),
            "value": round(row["avg_energy"], 2)
        }
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return {
        "kpis": {
            "avg_consumption": round(kpi.get("avg_energy") or 0, 2),
            "peak_usage": round(kpi.get("max_energy") or 0, 2),
            "min_usage": round(kpi.get("min_energy") or 0, 2),
            "renewable_share": round(kpi.get("renewable_share") or 0, 2)
        },
        "daily_consumption": daily_consumption,
        "hourly_profile": hourly_profile
    }

