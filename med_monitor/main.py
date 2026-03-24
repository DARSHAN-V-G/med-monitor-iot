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

    # ── Step 1: Get scan data ─────────────────────────────────────────────────
    if test_mode:
        from simulate_data import generate_scans
        print("Loading simulated scan data...")
        scans = load_simulated_scans()
        print(f"Loaded {len(scans)} simulated events.\n")
    else:
        from thingspeak_fetcher import fetch_scans
        channel_id = cfg.get("thingspeak_channel_id", "")
        api_key    = cfg.get("thingspeak_read_api_key", "")
        scans      = fetch_scans(channel_id, api_key, days=30)

        if not scans:
            print("[WARN] No ThingSpeak data. Falling back to simulated data.")
            scans = load_simulated_scans()

    # ── Step 2: Run ML analysis ───────────────────────────────────────────────
    from analyzer import run_analysis
    result = run_analysis(scans, config=cfg)

    if result is None:
        print("[WARN] Analysis returned no result. Not enough data yet.")
        return

    # ── Step 3: Check alert threshold ────────────────────────────────────────
    min_level    = cfg.get("alert_minimum_level", "WARNING")
    levels       = ["LOW", "WARNING", "HIGH"]
    result_level = result.get("risk_level", "LOW")

    should_alert = (
        levels.index(result_level) >= levels.index(min_level)
    )

    # ── Step 4: Save + notify (skip in test mode) ─────────────────────────────
    if test_mode:
        print("\n[TEST MODE] Skipping Firebase write and push notification.")
        print("  In live mode this result would be saved to Firestore.\n")
    else:
        creds_path = cfg.get("firebase_credentials", "serviceAccountKey.json")

        from firebase_writer import save_risk_result, send_push
        save_risk_result("medicine_001", result, credentials_path=creds_path)

        if should_alert:
            patient_name = cfg.get("patient_name", "Patient")
            send_push(patient_name, result_level, credentials_path=creds_path)
        else:
            print(f"Risk is {result_level} — below threshold. No alert sent.")

    # ── Step 5: Print summary ─────────────────────────────────────────────────
    print("\n── Pipeline Summary ────────────────────────────────────────")
    print(f"  Patient          : {cfg.get('patient_name', 'Unknown')}")
    print(f"  Risk level       : {result['risk_level']}")
    print(f"  Risk score       : {result['risk_score']}")
    print(f"  Drift per day    : {result['drift_minutes_per_day']} min")
    print(f"  Last dose        : {result['last_dose_time']} on {result['last_dose_date']}")
    print(f"  Tomorrow pred.   : {result['predicted_tomorrow_time']}")
    print(f"  Days tracked     : {result['total_days_tracked']}")
    print(f"  Detection method : {result['ml_method']}")
    print("────────────────────────────────────────────────────────────\n")

    return result


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
