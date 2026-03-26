# FRONTEND_IMPLEMENTATION_GUIDE.md

This document provides a **complete technical overview** for an AI or developer to build the "Med Monitor" mobile frontend (Flutter or React Native).

---

## 1. Project Context
**Med Monitor** is an IoT-based medication adherence system. It uses sensors to track when a patient picks up their medicine.
- **Goal**: Predict and prevent missed doses before they happen.
- **Ecosystem**: Hardware (ESP32/RFID) → IoT Platform (ThingSpeak) → Python AI/ML Backend → **Firebase (Firestore + FCM)** ← **Mobile App**.

---

## 2. Core Logic Overview (Context)
The backend uses **Z-Score** and **Isolation Forest** algorithms to monitor two variables:
1.  **Drift**: Is the patient taking the medicine ~15-30 minutes later each day?
2.  **Anomaly**: Is a single dose timing drastically different? (e.g., 3 hours late).

The backend calculates a **Risk Level** (`LOW`, `WARNING`, `HIGH`) and saves it to Firestore.

---

## 3. UI/UX & Design Language (Vibe check)
The mobile app must feel **Premium, Modern, and Medical-Grade**.
- **Visual Theme**: Dark Mode with Glassmorphism.
- **Colors**:
  - `Background`: Deep Slate/Navy (#0F172A).
  - `Risk LOW`: Vibrant Green (#22C55E).
  - `Risk WARNING`: Amber (#F59E0B).
  - `Risk HIGH`: Crimson (#EF4444).
- **Typography**: Clean Sans-Serif (e.g., `Inter`, `Manrope`, or `Outfit`).
- **Interaction**: Smooth micro-animations for transitions and "Medication Saved" feedback.

---

## 4. Firestore Data Schema
The app should listen to these Firestore collections using real-time streams.

### A. `risk_results/{medicine_id}`
| Field | Type | Description |
| :--- | :--- | :--- |
| `risk_level` | `String` | Use for the main Dashboard color & text. |
| `risk_score` | `Number` | 0-10+ (Visual adherence health indicator). |
| `drift` | `Number` | Minutes per day delay. |
| `predicted` | `String` | Predicted next dose time (`HH:MM`). |
| `last_dose` | `String` | Time of the most recent pickup. |
| `total_days` | `Number` | Patient history length. |

### B. `scan_history` (Audit Log)
- Each document represents an RFID scan.
- Sort by `logged_at` descending for the timeline view.
- Tag list entries with `event` ("present" or "absent").

### C. `medicines` (Config)
- **Flutter MUST WRITE** here to add a new medication.
- Contains: `name`, `tag_uid` (RFID card ID), `expected_time`, `frequency`.

---

## 5. Critical Workflows

### W1: Dashboard (Live Stream)
The main screen should show a big "Glassmorphic" card with the current Risk Level. If the status is `HIGH`, the card should pulse or provide a vibrate alert on entry.

### W2: "Learn New Bottle" (API Call)
To pair a new RFID tag without manually typing IDs:
1.  User clicks **"Detect Tag"** in the app.
2.  **Required Header**: `X-API-Key: <YOUR_SECRET_API_KEY>`
3.  App calls `HTTP GET http://<BACKEND_IP>:5000/detect-tag`.
4.  User scans the bottle on the physical RFID reader.
5.  The backend returns the `tag_uid`.
6.  App populates the registration form with this ID.

### W3: "Register Medicine" (API Call)
To save the new medicine to the system:
1.  App calls `HTTP POST http://<BACKEND_IP>:5000/add-medicine`.
2.  **Required Header**: `X-API-Key: <YOUR_SECRET_API_KEY>`
3.  **Payload**:
    ```json
    {
      "medicine_id": "medicine_002",
      "name": "Night Tablet",
      "tag_uid": "A3:B7:C2:D1",
      "expected_time": "20:00",
      "frequency": "daily"
    }
    ```
3.  **Response**: `{"status": "success", "message": "Medicine registration complete."}`

### W4: Push Notifications (FCM)
The app should subscribe to the **`family_alerts`** topic.
- Show a high-priority system notification if a `WARNING` or `HIGH` alert is received.
- Deep-link the notification directly to that specific medicine's detail page.

---

## 6. Development Checklist
- [ ] Initialize Firebase (Auth / Firestore / Messaging).
- [ ] Implement a real-time `StreamBuilder` for the Dashboard.
- [ ] Build a vertical scrollable Timeline for the `scan_history`.
- [ ] Implement the "Add Medicine" form with the `Detect Tag` API hook.
- [ ] Add the "Call Patient" or "Check In" quick-action buttons for `HIGH` risk alerts.
