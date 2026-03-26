# Med Monitor: Python Backend

This folder contains the ML analysis pipeline and the API for the Med Monitor project.

## Components

1.  **`main.py`**: The background worker. It fetches data from ThingSpeak, runs ML analysis via `analyzer.py`, and updates Firestore/sends Push Notifications.
2.  **`api.py`**: The Flask server. It provides endpoints for the mobile app to detect new RFID tags and register medicines.
3.  **`analyzer.py`**: The core ML logic (Z-Score + Isolation Forest).

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Firebase Credentials**: Place your `serviceAccountKey.json` in this folder.
3.  **Config**: Update `config.json` with your ThingSpeak orientation and a secure `api_key`.

## Running

### Background Analysis (The Worker)
To run the analysis once:
```bash
python main.py
```
To run it continuously (every 60 minutes):
```bash
python main.py --loop
```

### Mobile API Server (The Bridge)
To start the API for your Flutter/React Native app:
```bash
python api.py
```
The API will run on `http://localhost:5000`. 
*Note: Ensure you include the `X-API-Key` header for security.*

## Test Mode
To test the pipeline logic with simulated data without writing to Firebase:
```bash
python main.py --test
```
