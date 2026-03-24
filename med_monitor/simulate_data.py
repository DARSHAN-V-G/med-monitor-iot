"""
simulate_data.py
----------------
Generates fake 30-day medication scan data so you can test
the ML pipeline WITHOUT any hardware connected.

Normal pattern : 08:00 AM daily with small ±10 min random noise (days 1–25)
Drift pattern  : Last 5 days drift progressively later (the anomaly)

Run this first before anything else:
    python simulate_data.py

Output: saves simulated_scans.json in the same folder.
"""

import json
import random
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
TOTAL_DAYS        = 30       # How many days of history to generate
NORMAL_DAYS       = 25       # First N days are "normal"
BASE_HOUR         = 8        # Expected dose time: 8 AM
BASE_MINUTE       = 0
NOISE_MINUTES     = 10       # ±10 min random variation on normal days
DRIFT_PER_DAY     = 18       # Each drift day adds ~18 min (so day 5 = +90 min)
HOLD_DURATION_MIN = 5        # Minimum seconds bottle is held (realistic)
HOLD_DURATION_MAX = 30
TAG_UID           = "A3:B7:C2:D1"   # Fake RFID tag UID
MEDICINE_ID       = "medicine_001"
OUTPUT_FILE       = "simulated_scans.json"
# ─────────────────────────────────────────────────────────────────────────────


def generate_scans():
    scans = []
    start_date = datetime.now() - timedelta(days=TOTAL_DAYS)

    for day_index in range(TOTAL_DAYS):
        current_date = start_date + timedelta(days=day_index)

        # Calculate intake minute offset
        if day_index < NORMAL_DAYS:
            # Normal: small random noise around base time
            offset_minutes = random.randint(-NOISE_MINUTES, NOISE_MINUTES)
        else:
            # Drift: each day gets progressively later
            drift_day = day_index - NORMAL_DAYS + 1
            offset_minutes = drift_day * DRIFT_PER_DAY + random.randint(-5, 5)

        # Compute pickup time
        pickup_time = current_date.replace(
            hour=BASE_HOUR,
            minute=BASE_MINUTE,
            second=0,
            microsecond=0
        ) + timedelta(minutes=offset_minutes)

        # Compute put-back time (bottle held for a few seconds)
        hold_seconds = random.randint(HOLD_DURATION_MIN, HOLD_DURATION_MAX)
        putback_time = pickup_time + timedelta(seconds=hold_seconds)

        scans.append({
            "tag_uid":     TAG_UID,
            "medicine_id": MEDICINE_ID,
            "event":       "present",
            "timestamp":   pickup_time.isoformat(),
            "day_index":   day_index,
            "is_drift":    day_index >= NORMAL_DAYS
        })
        scans.append({
            "tag_uid":     TAG_UID,
            "medicine_id": MEDICINE_ID,
            "event":       "absent",
            "timestamp":   putback_time.isoformat(),
            "day_index":   day_index,
            "is_drift":    day_index >= NORMAL_DAYS
        })

    return scans


def main():
    print("Generating simulated scan data...")
    scans = generate_scans()

    with open(OUTPUT_FILE, "w") as f:
        json.dump(scans, f, indent=2)

    # Print summary
    print(f"\nGenerated {len(scans)} scan events ({TOTAL_DAYS} days)")
    print(f"Saved to: {OUTPUT_FILE}\n")
    print("Sample entries:")
    print(f"  Day 1  (normal): {scans[0]['timestamp']}")
    mid = NORMAL_DAYS * 2
    print(f"  Day 25 (normal): {scans[mid - 2]['timestamp']}")
    print(f"  Day 26 (drift ): {scans[mid]['timestamp']}")
    print(f"  Day 30 (drift ): {scans[-2]['timestamp']}")
    print("\nRun analyzer.py next to check if anomaly detection works.")


if __name__ == "__main__":
    main()
