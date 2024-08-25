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
from datetime import datetime, timezone

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dune API key
DUNE_API_KEY = 'p0RZJpTPCUn9Cn7UTXEWDhalc53QzZXV'

def check_table_exists():
    url = "https://api.dune.com/api/v1/table/list"
    headers = {
        "X-DUNE-API-KEY": DUNE_API_KEY
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        tables = response.json()
        return any(table['name'] == 'btc_etf_flow' for table in tables)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking table existence: {str(e)}")
        return False

def create_dune_table():
    if check_table_exists():
        logging.info("Table 'btc_etf_flow' already exists. Skipping creation.")
        return True

    url = "https://api.dune.com/api/v1/table/create"
    payload = {
        "namespace": "eekeyguy_eth",
        "table_name": "btc_etf_flow",
        "description": "BTC ETF Flow Data, sourced from CoinGlass",
        "schema": [
            {"name": "timestamp", "type": "timestamp"},
            {"name": "issuer", "type": "string"},
            {"name": "net_flow", "type": "double"},
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

@retry(stop_max_attempt_number=3, wait_fixed=2000)
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
        # Log the payload for debugging (be careful not to log sensitive data)
        logging.info(f"Payload preview: {payload['data'][:200]}...")
        
        response = requests.post(url, json=payload, headers=headers)
        
        # Log the response status and content
        logging.info(f"Response status code: {response.status_code}")
        logging.info(f"Response content: {response.text}")
        
        response.raise_for_status()
        logging.info("Data uploaded to Dune successfully")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error uploading to Dune: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response content: {e.response.text}")
        return False

def process_data(headers, rows):
    processed_data = []
    timestamp = datetime.now(timezone.utc).isoformat()
    for row in rows:
        for i, value in enumerate(row[1:8]):  # Skip 'Total' column
            if i == 0:  # GBTC
                continue  # Skip GBTC as per your request
            issuer = headers[i+1]
            try:
                net_flow = float(value.replace('+', '').replace('K', '000').replace(',', '')) if value.strip() else 0.0
            except ValueError:
                logging.warning(f"Could not convert '{value}' to float for issuer {issuer}. Setting to 0.")
                net_flow = 0.0
            aum = 0  # We don't have AUM data, so defaulting to 0
            market_share = 0  # We don't have market share data, so defaulting to 0
            processed_data.append([timestamp, issuer, net_flow, aum, market_share])
    return processed_data

def convert_to_csv(data):
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['timestamp', 'issuer', 'net_flow', 'aum', 'market_share'])
    csv_writer.writerows(data)
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
        # Create Dune table (or check if it exists)
        if not create_dune_table():
            logging.error("Failed to create or verify Dune table. Exiting.")
            return

        driver = webdriver.Chrome(options=chrome_options)
        logging.info("WebDriver initialized successfully")
        driver.get('https://www.coinglass.com/bitcoin-etf')
        logging.info("Page loaded")
        
        click_flows_tab(driver)
        headers, data_rows = get_table_data(driver)
        processed_data = process_data(headers, data_rows)
        csv_data = convert_to_csv(processed_data)
        
        # Log the full CSV data for debugging
        logging.info(f"Full CSV data:\n{csv_data}")
        
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
