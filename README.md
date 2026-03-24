# Preemptive Medication Adherence Monitor — Python Backend

This folder contains the entire Python software stack for the project.
It runs on your **laptop or PC** — not on the ESP32.

---

## What Each File Does

| File | Purpose | Run it when |
|---|---|---|
| `simulate_data.py` | Generates 30 days of fake RFID scan data | **First thing — before anything else** |
| `analyzer.py` | ML anomaly detection — detects timing drift | After simulate_data.py works |
| `firebase_writer.py` | Saves results to Firestore, sends push alerts | After Firebase is set up (Phase 1–2 of guide) |
| `thingspeak_fetcher.py` | Fetches real scan data from ThingSpeak | After hardware friend gives Channel ID + API Key |
| `main.py` | Runs the full pipeline end to end | After all above files are working |
| `config.json` | All your settings in one place | Edit before running main.py |
| `requirements.txt` | Python library list | Run once: `pip install -r requirements.txt` |
| `.gitignore` | Prevents secret keys going to GitHub | Already set up — don't touch |

---

## Quick Start (Do This First)

```bash
# Step 1: Install libraries
pip install -r requirements.txt

# Step 2: Generate fake data (no hardware needed)
python simulate_data.py

# Step 3: Test the ML detector
python analyzer.py

# Step 4: Run full pipeline in test mode (skips Firebase)
python main.py --test
```

You should see a risk level output like `WARNING` or `HIGH` on the last few days.
If you do — your ML pipeline is working correctly.

---

## How the ML Detection Works

```
Raw RFID timestamps
        │
        ▼
  extract_daily_intakes()   ← one pickup time per day
        │
        ├──▶ Z-score check    ← works from day 1 (5 lines of math)
        │
        └──▶ Isolation Forest ← kicks in after 7 days (sklearn)
                │
                ▼
         compute_risk_level()
                │
         ┌──────┴──────┐
         │             │
        LOW         WARNING / HIGH
         │             │
      (nothing)   send_push() → Telegram / FCM
```

### Risk Levels

| Level | What it means | Action |
|---|---|---|
| `LOW` | Normal pattern, no drift | Nothing — all good |
| `WARNING` | Drift starting, 1–2 anomalous days | Alert sent to family |
| `HIGH` | Significant drift, 3+ anomalous days | Urgent alert sent |

### Drift Detection Logic

- **Normal**: Grandma takes medicine at 8:00 AM ± 10 min every day
- **Warning sign**: Over 3 days, time shifts to 8:30 → 9:00 → 9:45
- **Prediction**: System calculates she'll take it at ~10:30 tomorrow
- **Preemptive alert**: Family is notified TODAY, not after tomorrow's miss

---

## Config Reference (`config.json`)

```json
{
  "patient_name": "Grandma",
  "thingspeak_channel_id": "from hardware friend",
  "thingspeak_read_api_key": "from hardware friend",
  "firebase_credentials": "serviceAccountKey.json",
  "alert_minimum_level": "WARNING",
  "check_interval_minutes": 60,
  "expected_dose_time": "08:00",
  "drift_warning_minutes": 30,
  "drift_high_minutes": 60,
  "anomaly_window_days": 7,
  "min_hold_duration_seconds": 5
}
```

`alert_minimum_level` — set to `"HIGH"` if family finds WARNING alerts too frequent.
`min_hold_duration_seconds` — pickups under 5s are flagged as suspicious (pill not actually taken).

---

## Run Modes

```bash
# Test mode — uses simulated data, skips Firebase writes
python main.py --test

# Live mode — fetches ThingSpeak, writes to Firebase
python main.py

# Loop mode — runs automatically every 60 minutes
python main.py --loop

# Test loop mode (simulated, runs repeatedly)
python main.py --test --loop
```

---

## Switching from Simulated to Real Hardware Data

When your hardware friend shares the ThingSpeak Channel ID and Read API Key:

1. Open `config.json`
2. Replace `"YOUR_CHANNEL_ID"` with the real channel ID
3. Replace `"YOUR_READ_API_KEY"` with the real API key
4. Run: `python main.py` (without `--test`)

The ML analysis code (`analyzer.py`) does not change at all.
Only the data source changes — everything else is identical.

---

## Firebase Setup (Phase 1–2 of Software Guide)

Before `firebase_writer.py` will work:

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create project → name it `MedMonitor`
3. Enable Firestore (region: `asia-south1`)
4. Enable Authentication → Email/Password
5. Project Settings → Service Accounts → Generate new private key
6. Download and rename the file to `serviceAccountKey.json`
7. Place `serviceAccountKey.json` in this folder (next to `main.py`)

**NEVER upload `serviceAccountKey.json` to GitHub.** It is already in `.gitignore`.

Test Firebase connection:
```bash
python firebase_writer.py
```

Check Firestore console — you should see `risk_results/medicine_001` appear.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: firebase_admin` | `pip install firebase-admin` |
| `ModuleNotFoundError: sklearn` | `pip install scikit-learn` |
| `serviceAccountKey.json not found` | Download from Firebase Console (see above) |
| `simulated_scans.json not found` | Run `python simulate_data.py` first |
| ThingSpeak returns empty | Hardware not connected yet — use `--test` mode |
| Risk always shows LOW | Check `analyzer.py` drift threshold — lower to 10 min |
| Push notification not received | Set up Flutter app first (Phase 4–6 of guide) |

---

## Data Flow (How Everything Connects)

```
ESP32 + RC522
     │  scans RFID tag on pill bottle
     │  sends timestamp to ThingSpeak
     ▼
ThingSpeak (cloud)
     │  stores field1=event, field2=tag_uid, field3=medicine_id
     │
     ▼
thingspeak_fetcher.py  ←──── OR ────  simulate_data.py
     │                                (for testing without hardware)
     ▼
analyzer.py  ←── ML anomaly detection
     │            Z-score + Isolation Forest
     │            outputs: risk_score, risk_level, drift, prediction
     ▼
firebase_writer.py
     ├──▶ Firestore → risk_results/medicine_001
     │                (Flutter reads this in real time)
     └──▶ FCM push notification → family's phone
```

---

## Team Handoff

- **Hardware team** → share ThingSpeak Channel ID + Read API Key
- **Flutter team** → reads `risk_results` collection from Firestore
- **Python team** → this folder is your entire responsibility

Python is the bridge. It's the only component that talks to both ThingSpeak and Firebase.
