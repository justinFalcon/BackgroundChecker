from flask import Blueprint, request, jsonify
import requests

ofac_bp = Blueprint("ofac", __name__)  # Ensure the correct blueprint name

OFAC_API_URL = "https://sanctionssearch.ofac.treas.gov/api/v1/search"

@ofac_bp.route("/check_ofac", methods=["GET"])
def check_ofac():
    """Checks OFAC Sanctions List for a given name."""
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "Missing 'name' parameter"}), 400

    response = requests.get(f"{OFAC_API_URL}?name={name}")
    
    if response.status_code == 200:
        return jsonify(response.json())  # Ensure correct response format
    else:
        return jsonify({"error": f"OFAC API Error: {response.status_code}"}), response.status_code
