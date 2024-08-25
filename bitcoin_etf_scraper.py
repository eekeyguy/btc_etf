import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime

# URL of the webpage
url = "https://farside.co.uk/bitcoin-etf-flow-all-data/"

# Send a GET request to the URL
response = requests.get(url)

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
