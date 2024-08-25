import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import cloudscraper
import json
from io import StringIO

def scrape_with_cloudscraper():
    url = "https://farside.co.uk/bitcoin-etf-flow-all-data/"
    
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox', 'platform': 'windows', 'mobile': False})
    
    for attempt in range(3):  # Try up to 3 times
        try:
            response = scraper.get(url)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
        time.sleep(10)  # Wait for 10 seconds before retrying
    
    return None

def extract_etf_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table = soup.find('table', class_='etf')
    
    if table:
        headers = [th.text.strip() for th in table.find_all('th')]
        rows = []
        for tr in table.find_all('tr')[1:]:
            row = [td.text.strip() for td in tr.find_all('td')]
            if row:
                rows.append(dict(zip(headers, row)))
        return rows
    else:
        print("Table with class 'etf' not found on the page.")
        return None

def convert_to_csv(data):
    csv_file = StringIO()
    if data:
        fieldnames = data[0].keys()
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(data)
        csv_data = csv_file.getvalue()
        csv_file.close()
        return csv_data
    return None

def upload_to_dune(csv_data):
    dune_upload_url = "https://api.dune.com/api/v1/table/upload/csv"
    payload = json.dumps({
        "data": csv_data,
        "description": "Bitcoin ETF Flow Data",
        "table_name": "bitcoin_etf_flow",
        "is_private": False
    })
    headers = {
        'Content-Type': 'application/json',
        'X-DUNE-API-KEY': 'p0RZJpTPCUn9Cn7UTXEWDhalc53QzZXV'
    }
    response = requests.post(dune_upload_url, headers=headers, data=payload)
    print(response.text)

def main():
    # Scrape data
    html_content = scrape_with_cloudscraper()
    
    if html_content:
        # Extract ETF data
        etf_data = extract_etf_data(html_content)
        
        if etf_data:
            # Convert to CSV
            csv_data = convert_to_csv(etf_data)
            
            if csv_data:
                # Upload to Dune
                upload_to_dune(csv_data)
            else:
                print("Failed to convert data to CSV.")
        else:
            print("Failed to extract ETF data.")
    else:
        print("Failed to retrieve the webpage after multiple attempts.")

if __name__ == "__main__":
    main()
