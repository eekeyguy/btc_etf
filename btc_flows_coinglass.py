import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from io import StringIO
import csv
import logging
from retrying import retry

# Set up logging
logging.basicConfig(level=logging.INFO)

# Dune API key
DUNE_API_KEY = 'p0RZJpTPCUn9Cn7UTXEWDhalc53QzZXV'

def create_dune_table():
    url = "https://api.dune.com/api/v1/table/create"
    payload = {
        "namespace": "eekeyguy_eth",  # Replace with your Dune username
        "table_name": "btc_etf_flow",
        "description": "BTC ETF Flow Data, sourced from CoinGlass",
        "schema": [
            {"name": "date", "type": "timestamp"},
            {"name": "issuer", "type": "string"},
            {"name": "net_flow", "type": "double"},
            {"name": "inflow", "type": "double"},
            {"name": "outflow", "type": "double"},
            {"name": "aum", "type": "double"},
            {"name": "market_share", "type": "double"}
        ],
        "is_private": False
    }
    headers = {
        "X-DUNE-API-KEY": DUNE_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logging.info(f"Dune table created successfully: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error creating Dune table: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response content: {e.response.text}")
        return False

def upload_to_dune(csv_data):
    url = "https://api.dune.com/api/v1/table/upload/csv"
    headers = {
        "X-DUNE-API-KEY": DUNE_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "table_name": "btc_etf_flow",
        "data": csv_data
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logging.info(f"Data uploaded to Dune successfully: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error uploading to Dune: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response content: {e.response.text}")
        return False

def convert_to_csv(headers, rows):
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(headers)
    for row in rows:
        csv_writer.writerow(row)
    csv_data = csv_file.getvalue()
    csv_file.close()
    return csv_data

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def click_flows_tab(driver):
    flows_tab_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Flows (USD)")]'))
    )
    flows_tab_button.click()
    logging.info("Flows (USD) tab clicked")

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def get_table_data(driver):
    WebDriverWait(driver, 20).until(
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
    return headers, data_rows

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Create Dune table
        if not create_dune_table():
            logging.error("Failed to create Dune table. Exiting.")
            return

        driver = webdriver.Chrome(options=chrome_options)
        logging.info("WebDriver initialized successfully")
        driver.get('https://www.coinglass.com/bitcoin-etf')
        logging.info("Page loaded")
        
        click_flows_tab(driver)
        headers, data_rows = get_table_data(driver)
        csv_data = convert_to_csv(headers, data_rows)
        
        # For debugging purposes, print a sample of the CSV data
        logging.info(f"Sample of CSV data: {csv_data[:200]}...")
        
        if upload_to_dune(csv_data):
            logging.info("Data successfully uploaded to Dune")
        else:
            logging.error("Failed to upload data to Dune")
    
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    
    finally:
        if 'driver' in locals():
            driver.quit()
            logging.info("WebDriver closed")

if __name__ == "__main__":
    main()
