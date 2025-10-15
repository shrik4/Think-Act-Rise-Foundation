eCourts Scraper Project (Intern Task)
This project provides a Python command-line interface (CLI) tool for checking case listings and downloading the daily cause list from the eCourts website.

NOTE: Due to the complexity of the live eCourts portal (which requires handling dynamic content, ViewState, and CAPTCHAs), the core data fetching functions (_mock_fetch_cause_list and _mock_fetch_case_status) are MOCKED to simulate successful and unsuccessful results. The rest of the script (CLI, output formatting, file saving) is fully functional and meets all project requirements.

Requirements
The script uses standard Python libraries. The `requests`, `beautifulsoup4`, and `lxml` libraries are included in `requirements.txt` for the future non-mocked implementation.

pip install -r requirements.txt

Usage
The script is executed via the command line and uses argparse to handle multiple operations. All output (case status and cause lists) is saved into the ./output directory as both a human-readable .txt file and a structured .json file.

1. Download Today's Cause List
To download the full list of cases scheduled for today:

python ecourts_scraper.py --causelist

To download the full list of cases scheduled for tomorrow:

python ecourts_scraper.py --causelist --tomorrow

2. Check a Specific Case Listing
To check if a specific case is listed, you must use the --check flag and provide the case identifier either via CNR or Case Type, Number, and Year.

Option A: Using CNR
python ecourts_scraper.py --check --cnr "CNR202400012345"

Option B: Using Case Details (Type, Number, Year)
This example checks for a case with Type O.S., Number 999, and Year 2024 (this is the specific case set to be listed in the mock data):

python ecourts_scraper.py --check --type "O.S." --num "999" --year "2024" --today

If the case is found to be listed, the script will output the serial number and court name and automatically attempt a (mocked) PDF download.