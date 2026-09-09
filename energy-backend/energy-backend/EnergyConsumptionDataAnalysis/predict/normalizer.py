FIELDS = {
    "Temperature": 0,
    "Humidity": 0,
    "Occupancy": 0,
    "SquareFootage": 0,
    "RenewableEnergy": 0,
    "HVAC": 0,
    "Lighting": 0,
    "Holiday": 0
}

def normalize(data: dict) -> dict:
    return {k: data.get(k, 0) or 0 for k in FIELDS}
