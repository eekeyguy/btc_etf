import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

# URL of the webpage
url = "https://farside.co.uk/bitcoin-etf-flow-all-data/"

# Headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Send a GET request to the URL with headers
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table with class 'etf'
    table = soup.find('table', class_='etf')

    if table:
        # Extract table headers
        headers = [th.text.strip() for th in table.find_all('th')]

        # Prepare data rows
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip the header row
            row = [td.text.strip() for td in tr.find_all('td')]
            if row:  # Ensure the row is not empty
                rows.append(row)

        # Generate a filename with current date and time
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_etf_flow_data_{current_time}.csv"

        # Write data to CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)

        print(f"Data has been scraped and saved to {filename}")
    else:
        print("Table with class 'etf' not found on the page.")
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    print(f"Response content: {response.text[:500]}...")  # Print first 500 characters of the response
