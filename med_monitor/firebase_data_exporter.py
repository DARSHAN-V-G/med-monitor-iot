"""
Firebase Data Exporter
Fetches all data from Firebase and exports to CSV and HTML visualization
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pandas as pd
from datetime import datetime
import json
import os

# Initialize Firebase (using serviceAccountKey.json)
SERVICE_ACCOUNT_KEY = "serviceAccountKey.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def fetch_risk_results():
    """Fetch all risk results from Firebase"""
    print("Fetching risk results...")
    risk_data = []
    try:
        docs = db.collection('risk_results').stream()
        for doc in docs:
            data = doc.to_dict()
            data['medicine_id'] = doc.id
            risk_data.append(data)
    except Exception as e:
        print(f"Error fetching risk results: {e}")
    return risk_data

def fetch_scan_history():
    """Fetch all scan history from Firebase"""
    print("Fetching scan history...")
    scan_data = []
    try:
        docs = db.collection('scan_history').order_by('logged_at', direction=firestore.Query.DESCENDING).stream()
        for doc in docs:
            data = doc.to_dict()
            data['scan_id'] = doc.id
            scan_data.append(data)
    except Exception as e:
        print(f"Error fetching scan history: {e}")
    return scan_data

def save_to_csv(risk_results, scan_history):
    """Save data to CSV files"""
    print("Saving to CSV files...")
    
    try:
        # Risk Results CSV
        if risk_results:
            risk_df = pd.DataFrame(risk_results)
            risk_csv = "firebase_risk_results.csv"
            risk_df.to_csv(risk_csv, index=False)
            print(f"✓ Risk results saved to {risk_csv}")
        
        # Scan History CSV
        if scan_history:
            scan_df = pd.DataFrame(scan_history)
            scan_csv = "firebase_scan_history.csv"
            scan_df.to_csv(scan_csv, index=False)
            print(f"✓ Scan history saved to {scan_csv}")
        
        return risk_df if risk_results else None, scan_df if scan_history else None
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        return None, None

def create_html_visualization(risk_df, scan_df):
    """Create HTML file with data visualization"""
    print("Creating HTML visualization...")
    
    # Summary statistics
    total_scans = len(scan_df) if scan_df is not None else 0
    
    risk_summary = ""
    if risk_df is not None and len(risk_df) > 0:
        high_risk = len(risk_df[risk_df.get('risk_level') == 'HIGH']) if 'risk_level' in risk_df.columns else 0
        low_risk = len(risk_df[risk_df.get('risk_level') == 'LOW']) if 'risk_level' in risk_df.columns else 0
        avg_score = risk_df['risk_score'].mean() if 'risk_score' in risk_df.columns else 0
        risk_summary = f"""
        <div class="stat-card">
            <h3>Total Medicines Monitored</h3>
            <p class="stat-value">{len(risk_df)}</p>
        </div>
        <div class="stat-card">
            <h3>High Risk Count</h3>
            <p class="stat-value danger">{high_risk}</p>
        </div>
        <div class="stat-card">
            <h3>Low Risk Count</h3>
            <p class="stat-value success">{low_risk}</p>
        </div>
        <div class="stat-card">
            <h3>Average Adherence Score</h3>
            <p class="stat-value">{avg_score:.2f}</p>
        </div>
        """
    
    scan_summary = f"""
    <div class="stat-card">
        <h3>Total Scans</h3>
        <p class="stat-value">{total_scans}</p>
    </div>
    """
    
    # Create risk results table
    risk_table = ""
    if risk_df is not None and len(risk_df) > 0:
        risk_table = "<table class='data-table'><thead><tr>"
        for col in risk_df.columns:
            risk_table += f"<th>{col}</th>"
        risk_table += "</tr></thead><tbody>"
        for idx, row in risk_df.iterrows():
            risk_table += "<tr>"
            for val in row:
                risk_table += f"<td>{val}</td>"
            risk_table += "</tr>"
        risk_table += "</tbody></table>"
    
    # Create scan history table
    scan_table = ""
    if scan_df is not None and len(scan_df) > 0:
        scan_table = "<table class='data-table'><thead><tr>"
        for col in scan_df.columns[:10]:  # Show first 10 columns
            scan_table += f"<th>{col}</th>"
        scan_table += "</tr></thead><tbody>"
        for idx, row in scan_df.head(50).iterrows():  # Show first 50 rows
            scan_table += "<tr>"
            for col in scan_df.columns[:10]:
                val = row[col]
                scan_table += f"<td>{val}</td>"
            scan_table += "</tr>"
        scan_table += "</tbody></table>"
    
    # HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Med Monitor - Firebase Data Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            header {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 30px;
            }}
            
            header h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }}
            
            header p {{
                color: #666;
                font-size: 1.1em;
            }}
            
            .timestamp {{
                color: #999;
                font-size: 0.9em;
                margin-top: 10px;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                text-align: center;
            }}
            
            .stat-card h3 {{
                color: #666;
                font-size: 0.95em;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 15px;
            }}
            
            .stat-value {{
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
            }}
            
            .stat-value.danger {{
                color: #ef4444;
            }}
            
            .stat-value.success {{
                color: #22c55e;
            }}
            
            .data-section {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 30px;
            }}
            
            .data-section h2 {{
                color: #333;
                margin-bottom: 20px;
                font-size: 1.8em;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }}
            
            .chart-container {{
                position: relative;
                height: 400px;
                margin-bottom: 30px;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            
            .data-table thead {{
                background: #667eea;
                color: white;
            }}
            
            .data-table th {{
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            
            .data-table td {{
                padding: 12px 15px;
                border-bottom: 1px solid #eee;
            }}
            
            .data-table tbody tr:hover {{
                background: #f5f5f5;
            }}
            
            .data-table tbody tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            
            footer {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                color: #666;
                margin-top: 30px;
            }}
            
            .no-data {{
                padding: 40px;
                text-align: center;
                color: #999;
                font-size: 1.1em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 Med Monitor - Firebase Dashboard</h1>
                <p>Real-time medication adherence monitoring system</p>
                <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </header>
            
            <div class="stats-grid">
                {risk_summary}
                {scan_summary}
            </div>
            
            <!-- Risk Results Section -->
            <div class="data-section">
                <h2>📋 Risk Results</h2>
                {risk_table if risk_table else "<div class='no-data'>No risk data available</div>"}
            </div>
            
            <!-- Scan History Section -->
            <div class="data-section">
                <h2>📱 Scan History (Last 50 Records)</h2>
                {scan_table if scan_table else "<div class='no-data'>No scan history available</div>"}
            </div>
            
            <footer>
                <p>Med Monitor IoT System • Firebase Data Export</p>
                <p>Data automatically synced from Firebase Firestore</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    html_file = "firebase_data_dashboard.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✓ HTML dashboard created: {html_file}")

def main():
    """Main execution"""
    print("=" * 60)
    print("Firebase Data Exporter for Med Monitor")
    print("=" * 60)
    
    # Fetch data
    risk_results = fetch_risk_results()
    scan_history = fetch_scan_history()
    
    print(f"\n✓ Fetched {len(risk_results)} risk records")
    print(f"✓ Fetched {len(scan_history)} scan records")
    
    # Save to CSV
    risk_df, scan_df = save_to_csv(risk_results, scan_history)
    
    # Create HTML visualization
    if risk_df is not None or scan_df is not None:
        create_html_visualization(risk_df, scan_df)
    
    print("\n" + "=" * 60)
    print("✓ Export completed successfully!")
    print("=" * 60)
    print("\nGenerated files:")
    print("  • firebase_risk_results.csv")
    print("  • firebase_scan_history.csv")
    print("  • firebase_data_dashboard.html (Open in browser)")
    print("=" * 60)

if __name__ == "__main__":
    main()
