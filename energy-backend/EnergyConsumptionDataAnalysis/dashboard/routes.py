from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from dashboard.services import get_dashboard_data

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/api/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    data = get_dashboard_data(str(get_jwt_identity()))
    return jsonify(data)
