import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from io import StringIO
import csv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

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
    logging.info(f"Dune API Response: {response.text}")

def convert_to_csv(headers, rows):
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(headers)
    for row in rows:
        csv_writer.writerow(row)
    csv_data = csv_file.getvalue()
    csv_file.close()
    return csv_data

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("WebDriver initialized successfully")

        driver.get('https://www.coinglass.com/bitcoin-etf')
        logging.info("Page loaded")

        # Wait for the "Flows (USD)" button to be clickable
        flows_tab_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Flows (USD)")]'))
        )
        flows_tab_button.click()
        logging.info("Flows (USD) tab clicked")

        # Wait for the table to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ant-table-tbody'))
        )
        logging.info("Table loaded")

        table = driver.find_element(By.CLASS_NAME, 'ant-table-tbody')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        headers = [header.text for header in driver.find_element(By.CLASS_NAME, 'ant-table-thead').find_elements(By.TAG_NAME, 'th')]

        data_rows = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            data = [cell.text for cell in cells]
            data_rows.append(data)

        csv_data = convert_to_csv(headers, data_rows)
        upload_to_dune(csv_data)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.quit()
            logging.info("WebDriver closed")

if __name__ == "__main__":
    main()
