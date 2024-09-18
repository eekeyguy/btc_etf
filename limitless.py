import requests
import json
import csv
from io import StringIO
from datetime import datetime

def fetch_market_data():
    url = "https://api.limitless.exchange/markets"
    response = requests.get(url)
    return response.json()

def extract_required_data(json_data):
    extracted_data = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    for item in json_data:
        extracted_item = {
            'date': current_date,
            'address': item['address'],
            'conditionId': item['conditionId'],
            'group_title': item['group'].get('title', 'N/A') if item['group'] else 'N/A',
            'title': item['title']
        }
        extracted_data.append(extracted_item)
    return extracted_data

def convert_to_csv(extracted_data):
    csv_file = StringIO()
    fieldnames = ['date', 'address', 'conditionId', 'group_title', 'title']
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    csv_writer.writeheader()
    csv_writer.writerows(extracted_data)
    csv_data = csv_file.getvalue()
    csv_file.close()
    return csv_data

def upload_to_dune(csv_data):
    dune_upload_url = "https://api.dune.com/api/v1/table/upload/csv"
    payload = json.dumps({
        "data": csv_data,
        "description": "Limitless Exchange Market Data",
        "table_name": "limitless_exchange_markets",
        "is_private": False
    })
    headers = {
        'Content-Type': 'application/json',
        'X-DUNE-API-KEY': 'p0RZJpTPCUn9Cn7UTXEWDhalc53QzZXV'
    }
    response = requests.post(dune_upload_url, headers=headers, data=payload)
    print(response.text)

def main():
    # Fetch market data
    json_data = fetch_market_data()
    
    # Extract required data
    extracted_data = extract_required_data(json_data)
    
    # Convert to CSV
    csv_data = convert_to_csv(extracted_data)
    
    # Upload to Dune
    upload_to_dune(csv_data)
    
    # Print the extracted data (optional, for verification)
    for item in extracted_data:
        print(json.dumps(item, indent=2))

if __name__ == "__main__":
    main()
