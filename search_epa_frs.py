import requests
import json

EPA_FRS_API_URL = "https://data.epa.gov/efservice"

def search_epa_frs(company_name):
    table = "FRS_PROGRAM_FACILITY"
    column = "PRIMARY_NAME"
    operator = "/CONTAINING/"
    format_type = "json"

    url = f"{EPA_FRS_API_URL}/{table}/{column}{operator}{company_name}/{format_type}"
    print(f"Fetching data from: {url}")  # Debugging statement

    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json()  # Convert response to JSON
            print("Raw EPA FRS Data:", json.dumps(data, indent=2))  # Debugging

            if not data:  # Check if empty response
                return []

            refined_results = []
            for facility in data:
                refined_results.append({
                    "FacilityName": facility.get("primary_name", "N/A"),  # Corrected key
                    "City": facility.get("city_name", "N/A"),  # Corrected key
                    "State": facility.get("state_code", "N/A"),  # Corrected key
                    "RegistryID": facility.get("registry_id", "N/A"),  # Corrected key
                    "FacilityURL": f"https://enviro.epa.gov/facts/facility/site.jsp?eparegistryid={facility.get('registry_id', '')}"
                })

            return refined_results

        except json.JSONDecodeError:
            print("Error parsing EPA FRS response. It might not be valid JSON.")
            return []
    else:
        print(f"EPA FRS API Error: {response.status_code} - {response.text}")
        return []
