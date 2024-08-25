import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from io import StringIO
import csv

def upload_to_dune(csv_data):
    dune_upload_url = "https://api.dune.com/api/v1/table/upload/csv"
    payload = json.dumps({
        "data": csv_data,
        "description": "Bitcoin ETF Flow Data",
        "table_name": "btc_etf_flow",
        "is_private": False
    })
    headers = {
        'Content-Type': 'application/json',
        'X-DUNE-API-KEY': 'p0RZJpTPCUn9Cn7UTXEWDhalc53QzZXV'
    }
    response = requests.post(dune_upload_url, headers=headers, data=payload)
    print(response.text)

def convert_to_csv(headers, rows):
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    
    # Write headers
    csv_writer.writerow(headers)
    
    # Write rows
    for row in rows:
        csv_writer.writerow(row)
    
    csv_data = csv_file.getvalue()
    csv_file.close()
    return csv_data

def main():
    # Set up the WebDriver
    driver = webdriver.Chrome()  # You can use Firefox() or any other driver

    # Load the page
    driver.get('https://www.coinglass.com/bitcoin-etf')

    # Wait for the page to load
    time.sleep(2)  # Wait for 2 seconds

    # Click the "Flows (USD)" button
    flows_tab_button = driver.find_element(By.XPATH, '//button[contains(text(), "Flows (USD)")]')
    flows_tab_button.click()

    # Wait for the table to load
    time.sleep(2)  # Wait for 2 seconds

    # Extract the table data
    table = driver.find_element(By.CLASS_NAME, 'ant-table-tbody')
    rows = table.find_elements(By.TAG_NAME, 'tr')

    # Extract table headers
    headers = [header.text for header in driver.find_element(By.CLASS_NAME, 'ant-table-thead').find_elements(By.TAG_NAME, 'th')]

    # Extract table rows
    data_rows = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        data = [cell.text for cell in cells]  # Extract the text from each cell
        data_rows.append(data)  # Add the row data to the list

    # Convert to CSV
    csv_data = convert_to_csv(headers, data_rows)

    # Upload to Dune
    upload_to_dune(csv_data)

    # Close the browser
    driver.quit()

if __name__ == "__main__":
    main()
