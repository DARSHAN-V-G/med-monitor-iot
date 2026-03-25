"""
firebase_writer.py
------------------
Handles all Firebase operations:
  - Saves ML risk results to Firestore (risk_results collection)
  - Reads medicine mappings from Firestore (medicines collection)
  - Sends push notifications via Firebase Cloud Messaging (FCM)

Requires:
  - serviceAccountKey.json in the same folder (download from Firebase Console)
  - pip install firebase-admin

DO NOT commit serviceAccountKey.json to GitHub.
Add it to .gitignore immediately.
"""

import firebase_admin
from firebase_admin import credentials, firestore, messaging


# ── Firebase initialization (runs once) ───────────────────────────────────────
_initialized = False

def _init_firebase(credentials_path: str = "serviceAccountKey.json"):
    global _initialized
    if not _initialized:
        try:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            _initialized = True
            print("Firebase initialized successfully.")
        except FileNotFoundError:
            print(f"[ERROR] {credentials_path} not found.")
            print("  Download it from Firebase Console:")
            print("  Project Settings → Service Accounts → Generate new private key")
            raise
        except Exception as e:
            print(f"[ERROR] Firebase init failed: {e}")
            raise
# ─────────────────────────────────────────────────────────────────────────────


def save_risk_result(medicine_id: str, result: dict, credentials_path: str = "serviceAccountKey.json"):
    """
    Saves ML analysis result to Firestore → risk_results collection.

    The Flutter dashboard reads this collection in real-time via StreamBuilder.
    Each medicine gets its own document (medicine_001, medicine_002, etc.)

    Args:
        medicine_id : document ID, e.g. "medicine_001"
        result      : dict from analyzer.run_analysis()
    """
    _init_firebase(credentials_path)
    db = firestore.client()

    doc_data = {
        "risk_score":              result.get("risk_score", 0),
        "risk_level":              result.get("risk_level", "LOW"),
        "drift":                   result.get("drift_minutes_per_day", 0.0),
        "last_dose":               result.get("last_dose_time", ""),
        "last_date":               result.get("last_dose_date", ""),
        "predicted":               result.get("predicted_tomorrow_time", ""),
        "recent_anomaly_count":    result.get("recent_anomaly_count", 0),
        "suspicious_pickups":      result.get("suspicious_pickups", 0),
        "total_days_tracked":      result.get("total_days_tracked", 0),
        "ml_method":               result.get("ml_method", "ZScore"),
        "updated_at":              firestore.SERVER_TIMESTAMP
    }

    db.collection("risk_results").document(medicine_id).set(doc_data)
    print(f"Saved risk result for {medicine_id} → Firestore")


def get_medicines(credentials_path: str = "serviceAccountKey.json") -> dict:
    """
    Reads the medicines collection from Firestore.
    Flutter writes to this when family adds a new tablet.
    Python reads it to know which tag_uid = which medicine.

    Returns:
        Dict of {medicine_id: {name, tag_uid, expected_time, frequency}}
    """
    _init_firebase(credentials_path)
    db = firestore.client()

    docs = db.collection("medicines").stream()
    medicines = {}
    for doc in docs:
        medicines[doc.id] = doc.to_dict()

    if not medicines:
        print("[INFO] No medicines found in Firestore yet.")
        print("  Add them via the Flutter app, or seed manually.")

    return medicines


def save_scan_event(tag_uid: str, event: str, timestamp: str, credentials_path: str = "serviceAccountKey.json"):
    """
    Optional: Saves individual scan events to Firestore scan_history.
    Useful for audit trail and Flutter history screen.

    Args:
        tag_uid   : RFID tag UID from ESP32
        event     : "present" or "absent"
        timestamp : ISO format datetime string
    """
    _init_firebase(credentials_path)
    db = firestore.client()

    db.collection("scan_history").add({
        "tag_uid":   tag_uid,
        "event":     event,
        "timestamp": timestamp,
        "logged_at": firestore.SERVER_TIMESTAMP
    })


def send_push(medicine_name: str, risk_level: str, credentials_path: str = "serviceAccountKey.json"):
    """
    Sends FCM push notification to all family members subscribed
    to the 'family_alerts' topic.

    Only sends for WARNING or HIGH risk — ignores LOW.

    Args:
        medicine_name : Patient name or medicine name for the alert body
        risk_level    : "LOW", "WARNING", or "HIGH"
    """
    if risk_level not in ("WARNING", "HIGH"):
        print(f"Risk level is {risk_level} — no push notification sent.")
        return

    _init_firebase(credentials_path)

    emoji = "⚠️" if risk_level == "WARNING" else "🚨"

    message = messaging.Message(
        notification=messaging.Notification(
            title=f"{emoji} Medication Alert",
            body=(
                f"{medicine_name}'s medication timing is becoming {risk_level.lower()}. "
                f"Please check in with the patient."
            )
        ),
        data={
            "risk_level":    risk_level,
            "medicine_name": medicine_name,
            "click_action":  "FLUTTER_NOTIFICATION_CLICK"
        },
        topic="family_alerts"   # Flutter app subscribes to this topic
    )

    try:
        response = messaging.send(message)
        print(f"Push notification sent. Message ID: {response}")
    except Exception as e:
        print(f"[ERROR] Failed to send push notification: {e}")
        print("  Make sure FCM is enabled in Firebase Console.")


def register_medicine(medicine_id: str, name: str, tag_uid: str, expected_time: str, frequency: str = "daily", credentials_path: str = "serviceAccountKey.json"):
    """
    Registers a new medicine in Firestore.
    Called by the Flask API when the user adds a new bottle.
    """
    _init_firebase(credentials_path)
    db = firestore.client()

    doc_data = {
        "name":          name,
        "tag_uid":       tag_uid,
        "expected_time": expected_time,
        "frequency":     frequency,
        "added_on":      firestore.SERVER_TIMESTAMP
    }

    db.collection("medicines").document(medicine_id).set(doc_data)
    print(f"Registered new medicine: {name} ({medicine_id}) → Firestore")


def seed_test_medicine(credentials_path: str = "serviceAccountKey.json"):
    """
    Seeds a test medicine document so you can test without the Flutter app.
    Run this once after Firebase is set up.
    """
    _init_firebase(credentials_path)
    db = firestore.client()

    db.collection("medicines").document("medicine_001").set({
        "name":          "Morning BP Tablet",
        "tag_uid":       "A3:B7:C2:D1",
        "expected_time": "08:00",
        "frequency":     "daily",
        "added_on":      firestore.SERVER_TIMESTAMP
    })
    print("Test medicine seeded to Firestore → medicines/medicine_001")


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Firebase connection...\n")

    test_result = {
        "risk_score":              2,
        "risk_level":              "WARNING",
        "drift_minutes_per_day":   18.0,
        "last_dose_time":          "09:45",
        "last_dose_date":          "2025-01-15",
        "predicted_tomorrow_time": "10:03",
        "recent_anomaly_count":    3,
        "suspicious_pickups":      0,
        "total_days_tracked":      30,
        "ml_method":               "IsolationForest+ZScore"
    }

    try:
        save_risk_result("medicine_001", test_result)
        print("\nFirebase write successful!")
        print("Check Firestore Console → risk_results → medicine_001")
    except FileNotFoundError:
        print("\nPlace serviceAccountKey.json in this folder first.")
