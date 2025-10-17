import argparse
import requests
import json
import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import time

app = Flask(__name__, static_folder='.') # Serve static files from the current directory
CORS(app)

# --- MOCK DATA FOR DEMONSTRATION ---
# In a real-world scenario, this data would come from POST requests to the eCourts server.
MOCK_CAUSE_LIST_DATA = {
    "Court1": [
        {"sn": 1, "case_type": "W.P.", "case_no": "123", "year": "2024", "party": "Ram vs. Shyam", "pdf_available": True},
        {"sn": 2, "case_type": "C.A.", "case_no": "456", "year": "2023", "party": "ABC Corp vs. Govt", "pdf_available": False},
        {"sn": 10, "case_type": "O.S.", "case_no": "999", "year": "2024", "party": "Case Target", "pdf_available": True},
    ],
    "Court2": [
        {"sn": 5, "case_type": "M.A.", "case_no": "101", "year": "2024", "party": "XYZ vs. PQR", "pdf_available": True},
    ]
}



MOCK_COURT_COMPLEXES = [
    {"id": "1", "name": "District Court, Delhi"},
    {"id": "2", "name": "High Court, Bombay"},
    {"id": "3", "name": "Supreme Court of India"},
    {"id": "4", "name": "District Court, Gurugram"},
    {"id": "5", "name": "High Court, Punjab and Haryana"},
    {"id": "6", "name": "District Court, Bengaluru"}
]

MOCK_JUDGES = [
    {"id": "J1", "name": "Justice A.K. Sharma", "complex_id": "1"},
    {"id": "J2", "name": "Justice B.N. Singh", "complex_id": "1"},
    {"id": "J3", "name": "Justice C.V. Rao", "complex_id": "2"},
    {"id": "J4", "name": "Justice D.E. Khan", "complex_id": "2"},
    {"id": "J5", "name": "Justice F.G. Patel", "complex_id": "3"},
    {"id": "J6", "name": "Justice H.I. Shah", "complex_id": "3"},
    {"id": "J7", "name": "Justice G.H. Singh", "complex_id": "4"},
    {"id": "J8", "name": "Justice I.J. Kumar", "complex_id": "4"},
    {"id": "J9", "name": "Justice K.L. Devi", "complex_id": "5"},
    {"id": "J10", "name": "Justice M.N. Prasad", "complex_id": "5"},
    {"id": "J11", "name": "Justice O.P. Gupta", "complex_id": "6"},
    {"id": "J12", "name": "Justice Q.R. Sharma", "complex_id": "6"}
]

def _mock_fetch_court_complexes():
    """
    Mocks the fetching of court complexes.
    """
    print("\n[MOCK] Fetching court complexes...")
    time.sleep(0.5) # Simulate network delay
    return MOCK_COURT_COMPLEXES

# --- CONFIGURATION ---
OUTPUT_DIR = "output"
# NOTE: The actual eCourts URL would be used here to send POST requests
ECOURTS_BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"

# --- UTILITY FUNCTIONS ---

def _mock_fetch_cause_list(date_str: str) -> dict:
    """
    Mocks the fetching of the cause list for a given date.
    """
    print(f"\n[MOCK] Fetching cause list for date: {date_str}...")
    # Simulate some delay
    time.sleep(1)

    # Return mock data for demonstration
    return {
        "case_list": [
            {
                "case_no": "C.C. No. 123/2025",
                "parties": "State vs. John Doe",
                "judge": "Justice A.K. Sharma",
                "stage": "Evidence",
                "next_hearing": "2025-10-15"
            },
            {
                "case_no": "S.T. No. 456/2025",
                "parties": "Jane Smith vs. David Lee",
                "judge": "Justice A.K. Sharma",
                "stage": "Arguments",
                "next_hearing": "2025-10-20"
            },
            {
                "case_no": "M.A. No. 789/2025",
                "parties": "Petitioner vs. Respondent",
                "judge": "Justice A.K. Sharma",
                "stage": "Orders",
                "next_hearing": "2025-10-25"
            }
        ],
        "summary": f"Mock cause list for {date_str} with 3 cases."
    }
    
    # Simulate an empty list for tomorrow, and a populated list for today
    if datetime.strptime(date_str, "%d-%m-%Y").date() == datetime.now().date():
        return MOCK_CAUSE_LIST_DATA
    else:
        return {} # No list found for other dates

def _mock_fetch_case_status(case_identifier: dict, date_str: str) -> dict:
    """
    Mocks the fetching of a specific case status for a given date.
    
    In a real implementation, this would involve:
    1. Submitting the case details (CNR/Type/No/Year) via a POST request.
    2. Parsing the results to see if a listing matches the required date.
    """
    print(f"[MOCK] Checking listing for {case_identifier} on {date_str}...")
    
    # Simulate a successful match only for the specific mock case on today's date
    target_case = {"case_type": "O.S.", "case_no": "999", "year": "2024"}
    
    if (case_identifier.get('case_type') == target_case['case_type'] and
        case_identifier.get('case_no') == target_case['case_no'] and
        case_identifier.get('year') == target_case['year'] and
        datetime.strptime(date_str, "%d-%m-%Y").date() == datetime.now().date()):
        
        return {
            "is_listed": True,
            "court_name": "Court2",
            "serial_number": 10,
            "pdf_link_mock": f"case_{case_identifier.get('case_type')}_{case_identifier.get('case_no')}.pdf"
        }
    
    return {"is_listed": False}

# --- CORE LOGIC FUNCTIONS ---

def check_case_listing(case_details: dict, date_check: str):
    """
    Checks if a specific case is listed on today or tomorrow.
    
    :param case_details: Dictionary containing CNR or (Type, Number, Year).
    :param date_check: 'today' or 'tomorrow'.
    """
    today = datetime.now()
    if date_check == 'today':
        target_date = today
    elif date_check == 'tomorrow':
        target_date = today + timedelta(days=1)
    else:
        print("Error: Invalid date_check parameter.")
        return

    date_str = target_date.strftime("%d-%m-%Y")

    print(f"\n--- Checking Case Listing for {date_str} ({date_check.upper()}) ---")
    
    result = _mock_fetch_case_status(case_details, date_str)

    if result.get("is_listed"):
        output = (
            f"✅ CASE IS LISTED on {date_str}!\n"
            f"   Court Name: {result['court_name']}\n"
            f"   Serial No.: {result['serial_number']}\n"
        )
        print(output)
        
        # Save individual case result
        filename_base = f"case_status_{date_check}"
        save_results(output, result, filename_base)
        
        # Check for PDF option
        if result.get("pdf_link_mock"):
            download_case_pdf(case_details, result['pdf_link_mock'])
            
    else:
        output = f"❌ Case NOT listed on {date_str}."
        print(output)
        save_results(output, {"is_listed": False}, f"case_status_{date_check}")


def download_cause_list(date_check: str):
    """
    Downloads and saves the entire cause list for the specified date.
    
    :param date_check: 'today' or 'tomorrow'.
    """
    today = datetime.now()
    if date_check == 'today':
        target_date = today
    elif date_check == 'tomorrow':
        target_date = today + timedelta(days=1)
    else:
        print("Error: Invalid date_check parameter.")
        return
        
    date_str = target_date.strftime("%d-%m-%Y")
    
    print(f"\n--- Downloading Cause List for {date_str} ({date_check.upper()}) ---")

    cause_list_data = _mock_fetch_cause_list(date_str)
    
    if not cause_list_data:
        output = f"⚠️ No cause list found for {date_str}."
        print(output)
        save_results(output, {}, f"cause_list_{date_check}")
        return

    text_output = [f"CAUSE LIST FOR: {date_str}\n" + "="*50]
    
    for court_name, cases in cause_list_data.items():
        text_output.append(f"\nCOURT: {court_name}")
        text_output.append("-" * 20)
        for case in cases:
            pdf_status = "(PDF Available)" if case.get("pdf_available") else "(No PDF)"
            line = (f"  SN: {case['sn']:<3} | {case['case_type']:<5} {case['case_no']:<4}/{case['year']} "
                    f"| {case['party']:<30} {pdf_status}")
            text_output.append(line)
            
    final_text_output = "\n".join(text_output)
    print(final_text_output)

    # Save results
    save_results(final_text_output, cause_list_data, f"cause_list_{date_check}")
    
def download_case_pdf(cause_list_data: list):
    """
    Generates a PDF for a cause list.
    """
    pdf_filename = f"cause_list_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    
    print(f"\n[MOCK] Attempting to generate PDF for cause list...")
    
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        y_position = 750

        if not cause_list_data:
            p.drawString(100, y_position, "No cause list data available.")
            y_position -= 20
        else:
            for case in cause_list_data:
                for key, value in case.items():
                    p.drawString(100, y_position, f"{key.replace('_', ' ').title()}: {value}")
                    y_position -= 15
                y_position -= 10  # Add a small gap between cases
                if y_position < 50:  # Add new page if content goes too low
                    p.showPage()
                    y_position = 750

        p.showPage()
        p.save()
        
        buffer.seek(0)
        
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        with open(os.path.join(OUTPUT_DIR, pdf_filename), 'wb') as f:
            f.write(buffer.getvalue())
            
        print(f"   PDF successfully generated and saved as: {OUTPUT_DIR}/{pdf_filename}")
        return os.path.join(OUTPUT_DIR, pdf_filename)
    except Exception as e:
        print(f"   Error generating/saving PDF: {e}")
        return None


# --- FILE SAVING UTILITY ---

def save_results(text_content: str, json_content: dict, filename_base: str):
    """Saves results to both a JSON and a text file."""
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # Save as JSON
    json_path = os.path.join(OUTPUT_DIR, f"{filename_base}.json")
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_content, f, indent=4)
        print(f"\n[SAVED] Structured JSON result saved to: {json_path}")
    except Exception as e:
        print(f"[ERROR] Could not save JSON file: {e}")

    # Save as Text
    text_path = os.path.join(OUTPUT_DIR, f"{filename_base}.txt")
    try:
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text_content)
        print(f"[SAVED] Console output saved to: {text_path}")
    except Exception as e:
        print(f"[ERROR] Could not save Text file: {e}")

# --- MAIN CLI INTERFACE ---



@app.route('/api/court_complexes')
def get_court_complexes():
    return jsonify(_mock_fetch_court_complexes())

@app.route('/api/judges')
def get_judges():
    complex_id = request.args.get('complex_id')
    if complex_id:
        filtered_judges = [judge for judge in MOCK_JUDGES if judge['complex_id'] == complex_id]
        return jsonify(filtered_judges)
    return jsonify(MOCK_JUDGES)

@app.route('/api/cause_list', methods=['POST'])
def api_cause_list():
    data = request.get_json()
    date_check = data.get('date_check', 'today')
    cause_list_data = _mock_fetch_cause_list(date_check)
    return jsonify(cause_list_data)

@app.route('/api/case_status', methods=['POST'])
def api_case_status():
    data = request.get_json()
    case_details = data.get('case_details')
    date_check = data.get('date_check', 'today')
    result = _mock_fetch_case_status(case_details, date_check)
    return jsonify(result)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/download_pdf', methods=['POST'])
def api_download_pdf():
    data = request.get_json()
    judge_name = data.get('judge_name')
    complex_name = data.get('complex_name')
    date = data.get('date')

    # For demonstration, we'll use a mock case_details and mock_link
    date = data.get('date')

    # Fetch the mock cause list data
    cause_list_response = _mock_fetch_cause_list(date)
    cause_list_data = cause_list_response.get("case_list", [])

    pdf_path = download_case_pdf(cause_list_data)
    if pdf_path:
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
    else:
        return jsonify({"message": "Failed to generate PDF"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
