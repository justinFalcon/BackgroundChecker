import requests
import json
from flask import Flask, render_template, request, redirect, url_for
from search_epa_frs import search_epa_frs  # Import function from search_epa_frs.py
from search_ofac import ofac_bp  # Import the OFAC API blueprint

app = Flask(__name__)

# Register the OFAC API Blueprint
app.register_blueprint(ofac_bp, url_prefix="/ofac")

# API Endpoints
GLEIF_API_URL = "https://api.gleif.org/api/v1/lei-records"
SEC_BASE_URL = "https://data.sec.gov/submissions/"
SEC_CIK_SEARCH_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANIES_HOUSE_API_URL = "https://api.company-information.service.gov.uk/search/companies"

COMPANIES_HOUSE_API_KEY = "YOUR_COMPANIES_HOUSE_API_KEY"

HEADERS = {
    "User-Agent": "MyCompanySearchApp/1.0 (contact@mydomain.com)"
}

BRAND_MAPPING = {
    "google": "alphabet inc",
    "facebook": "meta platforms inc",
    "twitter": "x corp",
    "square": "block inc",
    "snapchat": "snap inc",
}

def search_gleif(company_name):
    """Searches the GLEIF API for a company name."""
    url = f"{GLEIF_API_URL}?filter[entity.legalName]={company_name}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("data", [])
    return []

def get_cik(company_name):
    """Fetches the CIK number for a given company name."""
    response = requests.get(SEC_CIK_SEARCH_URL, headers=HEADERS)
    if response.status_code == 200:
        try:
            cik_data = response.json()
            company_name_lower = BRAND_MAPPING.get(company_name.lower(), company_name.lower())
            for entry in cik_data.values():
                if company_name_lower in entry["title"].lower():
                    return str(entry["cik_str"]).zfill(10)
        except json.JSONDecodeError:
            pass
    return None

def search_sec(company_name):
    """Searches the SEC EDGAR database using CIK."""
    cik = get_cik(company_name)
    if cik:
        response = requests.get(f"{SEC_BASE_URL}CIK{cik}.json", headers=HEADERS)
        if response.status_code == 200:
            try:
                return response.json().get("filings", {}).get("recent", [])
            except json.JSONDecodeError:
                pass
    return []

def search_companies_house(company_name):
    """Searches UK Companies House for a given company name."""
    headers = {"Authorization": COMPANIES_HOUSE_API_KEY}
    response = requests.get(f"{COMPANIES_HOUSE_API_URL}?q={company_name}", headers=headers)
    if response.status_code == 200:
        return response.json().get("items", [])
    return []

@app.route("/", methods=["GET", "POST"])
def home():
    """Handles the home page and search form submission."""
    if request.method == "POST":
        company_name = request.form.get("query", "").strip()
        company_name = BRAND_MAPPING.get(company_name.lower(), company_name)
        sources = request.form.getlist("sources")  # Corrected to use getlist() for multiple selections
        return redirect(url_for("results", query=company_name, sources=','.join(sources)))
    return render_template("search.html")

@app.route("/results")
def results():
    """Handles search results display."""
    company_name = request.args.get("query", "").strip()
    selected_sources = request.args.get("sources", "").split(',')
    results = {}

    # Fetch data from each selected source
    if "GLEIF" in selected_sources:
        results["GLEIF"] = search_gleif(company_name)

    if "SEC EDGAR" in selected_sources:
        results["SEC EDGAR"] = search_sec(company_name)

    if "Companies House" in selected_sources:
        results["Companies House"] = search_companies_house(company_name)

    if "EPA FRS" in selected_sources:
        try:
            epa_results = search_epa_frs(company_name)
            results["EPA FRS"] = epa_results if isinstance(epa_results, list) else []
        except Exception as e:
            results["EPA FRS"] = [f"EPA FRS API Error: {str(e)}"]

    # OFAC Sanctions Check with Debugging and Error Handling
    if "OFAC Sanctions" in selected_sources:
        try:
            ofac_url = f"http://127.0.0.1:5000/ofac/check_ofac?name={company_name}"
            ofac_response = requests.get(ofac_url)
            
            if ofac_response.status_code == 200:
                ofac_data = ofac_response.json()
                print("OFAC Response:", json.dumps(ofac_data, indent=2))  # Debugging
                
                if isinstance(ofac_data, dict) and "match_found" in ofac_data:
                    results["OFAC Sanctions"] = ofac_data.get("results", ["No matches found"])
                else:
                    results["OFAC Sanctions"] = ["Unexpected data format"]
            else:
                results["OFAC Sanctions"] = [f"OFAC API Error: {ofac_response.status_code}"]
        except Exception as e:
            results["OFAC Sanctions"] = [f"OFAC API Error: {str(e)}"]

    return render_template("results.html", results=results, query=company_name)


if __name__ == "__main__":
    app.run(debug=True)
