"""
thingspeak_fetcher.py
---------------------
Fetches real RFID scan data from ThingSpeak once your hardware
friend gives you the Channel ID and Read API Key.

ThingSpeak channel field mapping (agreed with hardware team):
  field1 = event type   ("present" or "absent")
  field2 = tag_uid      (e.g. "A3:B7:C2:D1")
  field3 = medicine_id  (e.g. "medicine_001")

Until hardware is ready, the main.py uses simulate_data.py instead.
Just swap the import when hardware is connected.

Usage:
    from thingspeak_fetcher import fetch_scans
    scans = fetch_scans(channel_id, api_key, days=30)
"""

import requests
from datetime import datetime, timedelta


THINGSPEAK_BASE = "https://api.thingspeak.com"


def fetch_scans(channel_id: str, api_key: str, days: int = 30) -> list:
    """
    Fetches scan entries from ThingSpeak for the past N days.

    Args:
        channel_id : ThingSpeak channel ID (from hardware team)
        api_key    : ThingSpeak Read API Key (from hardware team)
        days       : How many days of history to fetch (default 30)

    Returns:
        List of scan dicts matching the same format as simulate_data.py
        so analyzer.py works with both without any changes.
    """
    if channel_id == "YOUR_CHANNEL_ID":
        print("[WARN] ThingSpeak channel ID not set in config.json")
        print("       Using simulated data instead.")
        return []

    # ThingSpeak allows max 8000 results per call
    # Calculate start date
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    url = (
        f"{THINGSPEAK_BASE}/channels/{channel_id}/feeds.json"
        f"?api_key={api_key}&start={start_date}&results=8000"
    )

    print(f"Fetching ThingSpeak data for last {days} days...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot reach ThingSpeak. Check internet connection.")
        return []
    except requests.exceptions.Timeout:
        print("[ERROR] ThingSpeak request timed out.")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] ThingSpeak returned error: {e}")
        return []

    data = response.json()
    feeds = data.get("feeds", [])

    if not feeds:
        print("[WARN] No data returned from ThingSpeak.")
        print("       Has the ESP32 sent any scans yet?")
        return []

    print(f"  Fetched {len(feeds)} raw entries from ThingSpeak")

    # Convert ThingSpeak feed format → our internal scan format
    scans = []
    for feed in feeds:
        field1 = feed.get("field1", "").strip()  # event
        field2 = feed.get("field2", "").strip()  # tag_uid
        field3 = feed.get("field3", "").strip()  # medicine_id

        if not field1 or not field2:
            continue  # skip incomplete entries

        # ThingSpeak timestamps are UTC — keep as-is
        scans.append({
            "tag_uid":     field2,
            "medicine_id": field3 or "medicine_001",
            "event":       field1.lower(),
            "timestamp":   feed.get("created_at", ""),
            "day_index":   None,
            "is_drift":    False  # analyzer will determine this
        })

    print(f"  Parsed {len(scans)} valid scan events")
    return scans


def fetch_latest_tag_uid(channel_id: str, api_key: str) -> str:
    """
    Fetches the most recent tag UID scanned.
    Used by Flutter's 'Detect Tag' button via Python API endpoint.

    Returns tag_uid string or empty string if none found.
    """
    url = (
        f"{THINGSPEAK_BASE}/channels/{channel_id}/feeds.json"
        f"?api_key={api_key}&results=1"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        feeds = data.get("feeds", [])
        if feeds:
            return feeds[0].get("field2", "").strip()
    except Exception as e:
        print(f"[ERROR] Could not fetch latest tag UID: {e}")

    return ""


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json

    # Replace these with real values from your hardware friend
    TEST_CHANNEL = "YOUR_CHANNEL_ID"
    TEST_KEY     = "YOUR_READ_API_KEY"

    scans = fetch_scans(TEST_CHANNEL, TEST_KEY, days=30)
    if scans:
        print("\nFirst scan entry:")
        print(json.dumps(scans[0], indent=2))
        print(f"\nLast scan entry:")
        print(json.dumps(scans[-1], indent=2))
    else:
        print("No scans fetched — hardware might not be connected yet.")
