from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging

from thingspeak_fetcher import fetch_latest_tag_uid
from firebase_writer import register_medicine
from main import load_config

app = Flask(__name__)
CORS(app)  # Allow Flutter/React Native to call this API

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load config once on startup
cfg = load_config()

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "running", "service": "Med Monitor API"})

@app.route("/detect-tag", methods=["GET"])
def detect_tag():
    """
    Fetches the most recent RFID tag UID scanned.
    Used by the 'Learn Tag' feature in the mobile app.
    """
    channel_id = cfg.get("thingspeak_channel_id")
    api_key    = cfg.get("thingspeak_read_api_key")

    logger.info("Fetching latest tag from ThingSpeak...")
    tag_uid = fetch_latest_tag_uid(channel_id, api_key)

    if tag_uid:
        return jsonify({
            "status": "success",
            "tag_uid": tag_uid
        })
    else:
        return jsonify({
            "status": "error",
            "message": "No recent tag detected. Please scan physical bottle now."
        }), 404

@app.route("/add-medicine", methods=["POST"])
def add_medicine():
    """
    Registers a new medicine in Firestore.
    Expects JSON: {medicine_id, name, tag_uid, expected_time, frequency}
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Missing JSON body"}), 400

    required = ["medicine_id", "name", "tag_uid", "expected_time"]
    for field in required:
        if field not in data:
            return jsonify({"status": "error", "message": f"Missing field: {field}"}), 400

    try:
        register_medicine(
            medicine_id=data["medicine_id"],
            name=data["name"],
            tag_uid=data["tag_uid"],
            expected_time=data["expected_time"],
            frequency=data.get("frequency", "daily"),
            credentials_path=cfg.get("firebase_credentials", "serviceAccountKey.json")
        )
        return jsonify({"status": "success", "message": f"Medicine {data['name']} registered."})
    except Exception as e:
        logger.error(f"Failed to register medicine: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # In production, use a real server like Gunicorn or Waitress
    logger.info("Starting Med Monitor API on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=True)
