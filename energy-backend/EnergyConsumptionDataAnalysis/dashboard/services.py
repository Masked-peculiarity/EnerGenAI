"""User-scoped dashboard summaries of saved model predictions."""

from contextlib import closing

from db import get_connection


def get_dashboard_data(username):
    with closing(get_connection()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS prediction_count,
                       AVG(energyconsumption) AS avg_energy,
                       MAX(energyconsumption) AS max_energy,
                       MIN(energyconsumption) AS min_energy,
                       CASE WHEN SUM(energyconsumption) > 0
                            THEN 100.0 * SUM(renewableenergy) / SUM(energyconsumption)
                            ELSE 0 END AS renewable_share
                FROM energy_history
                WHERE username = %s AND timestamp >= NOW() - INTERVAL '7 days'
                """,
                (username,),
            )
            kpi = cursor.fetchone() or {}

            cursor.execute(
                """
                SELECT DATE(timestamp AT TIME ZONE 'UTC') AS day,
                       AVG(energyconsumption) AS avg_energy
                FROM energy_history
                WHERE username = %s AND timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY day ORDER BY day
                """,
                (username,),
            )
            daily = [
                {"day": row["day"].strftime("%b %d"), "value": round(float(row["avg_energy"]), 2)}
                for row in cursor.fetchall()
            ]

            cursor.execute(
                """
                SELECT EXTRACT(HOUR FROM timestamp AT TIME ZONE 'UTC') AS hour,
                       AVG(energyconsumption) AS avg_energy
                FROM energy_history
                WHERE username = %s AND timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY hour ORDER BY hour
                """,
                (username,),
            )
            hourly = [
                {"hour": int(row["hour"]), "value": round(float(row["avg_energy"]), 2)}
                for row in cursor.fetchall()
            ]

    share = float(kpi.get("renewable_share") or 0)
    return {
        "kpis": {
            "prediction_count": int(kpi.get("prediction_count") or 0),
            "avg_consumption": round(float(kpi.get("avg_energy") or 0), 2),
            "peak_usage": round(float(kpi.get("max_energy") or 0), 2),
            "min_usage": round(float(kpi.get("min_energy") or 0), 2),
            "renewable_share": round(max(0, min(100, share)), 2),
        },
        "daily_consumption": daily,
        "hourly_profile": hourly,
    }
