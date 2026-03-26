"""
main.py
-------
Pipeline orchestrator — runs the full system end to end.

Flow:
  1. Load config.json
  2. Fetch scan data  → ThingSpeak (real) or simulated_scans.json (test)
  3. Run ML analysis  → analyzer.py
  4. Save result      → Firebase Firestore via firebase_writer.py
  5. Send alert       → FCM push notification if WARNING/HIGH

Run modes:
  python main.py            → live mode (ThingSpeak + Firebase)
  python main.py --test     → test mode (simulated data, skips Firebase)
  python main.py --loop     → runs every N minutes (set in config.json)

Start here after simulate_data.py and analyzer.py work correctly.
"""

import json
import time
import argparse
from datetime import datetime


def load_config(path: str = "config.json") -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] {path} not found. Create it from the template.")
        exit(1)


def load_simulated_scans(path: str = "simulated_scans.json") -> list:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] simulated_scans.json not found.")
        print("  Run first:  python simulate_data.py")
        exit(1)


def run_pipeline(cfg: dict, test_mode: bool = False):
    """
    Single pipeline run. Called once (or in a loop for --loop mode).
    """
    print(f"\n{'='*55}")
    print(f"  Med Monitor Pipeline  —  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Mode: {'TEST (simulated data)' if test_mode else 'LIVE (ThingSpeak)'}")
    print(f"{'='*55}\n")

    creds_path = cfg.get("firebase_credentials", "serviceAccountKey.json")
    from firebase_writer import save_risk_result, send_push, get_medicines

    # ── Step 1: Get data + medicine mapping ───────────────────────────────────
    if test_mode:
        print("Loading simulated scan data...")
        all_scans = load_simulated_scans()
        # Mock medicine mapping for test mode
        medicines = {
            "medicine_001": {"name": cfg.get("patient_name", "Patient"), "tag_uid": "A3:B7:C2:D1"}
        }
    else:
        # Fetch actual medicine registry from Firestore
        medicines = get_medicines(credentials_path=creds_path)
        if not medicines:
            print("[WARN] No medicines found in Firestore. Check your configuration.")
            return

        from thingspeak_fetcher import fetch_scans
        channel_id = cfg.get("thingspeak_channel_id", "")
        api_key    = cfg.get("thingspeak_read_api_key", "")
        all_scans  = fetch_scans(channel_id, api_key, days=60)

        if not all_scans:
            print("[WARN] No ThingSpeak data. Falling back to simulated data.")
            all_scans = load_simulated_scans()

    # ── Step 2: Loop through each medicine and analyze ────────────────────────
    from analyzer import run_analysis
    
    for med_id, med_info in medicines.items():
        med_name = med_info.get("name", "Unknown")
        tag_uid  = med_info.get("tag_uid", "")
        
        print(f"\n--- Analyzing: {med_name} ({med_id}) ---")
        
        # Filter scans for this specific medicine's tag
        med_scans = [s for s in all_scans if s.get("tag_uid") == tag_uid]
        
        if not med_scans:
            print(f"  [SKIP] No scan data found for tag {tag_uid}.")
            continue

        result = run_analysis(med_scans, config=cfg)

        if result is None:
            print(f"  [WARN] Not enough data for {med_name} yet.")
            continue

        # ── Step 3: Risk Assessment + Output ──────────────────────────────────
        min_level    = cfg.get("alert_minimum_level", "WARNING")
        levels       = ["LOW", "WARNING", "HIGH"]
        result_level = result.get("risk_level", "LOW")
        should_alert = levels.index(result_level) >= levels.index(min_level)

        if test_mode:
            print(f"  [TEST] Risk level: {result_level}. Skipping Firebase save.")
        else:
            save_risk_result(med_id, result, credentials_path=creds_path)

            if should_alert:
                send_push(med_name, result_level, credentials_path=creds_path)
            else:
                print(f"  Risk is {result_level} — below threshold. No alert sent.")

        # ── Step 4: Print Summary ─────────────────────────────────────────────
        print(f"  Result: {result_level} (Score={result['risk_score']})")
        print(f"  Drift: {result['drift_minutes_per_day']} min/day")
        print(f"  Prediction: {result['predicted_tomorrow_time']}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Med Monitor Pipeline")
    parser.add_argument("--test",  action="store_true", help="Use simulated data, skip Firebase")
    parser.add_argument("--loop",  action="store_true", help="Run continuously every N minutes")
    args = parser.parse_args()

    cfg = load_config()

    if args.loop:
        interval = cfg.get("check_interval_minutes", 60) * 60
        print(f"Loop mode: running every {cfg.get('check_interval_minutes', 60)} minutes.")
        print("Press Ctrl+C to stop.\n")
        while True:
            try:
                run_pipeline(cfg, test_mode=args.test)
                print(f"Sleeping {cfg.get('check_interval_minutes', 60)} minutes...\n")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\nStopped by user.")
                break
    else:
        run_pipeline(cfg, test_mode=args.test)


if __name__ == "__main__":
    main()
