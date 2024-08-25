import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from io import StringIO
import csv
import logging
from retrying import retry

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dune API key
DUNE_API_KEY = 'p0RZJpTPCUn9Cn7UTXEWDhalc53QzZXV'

def upload_to_dune(csv_data):
    dune_upload_url = "https://api.dune.com/api/v1/table/upload/csv"
    payload = json.dumps({
        "data": csv_data,
        "description": "BTC ETF Flow Data",
        "table_name": "btc_etf_flow",
        "is_private": False
    })
    headers = {
        'Content-Type': 'application/json',
        'X-DUNE-API-KEY': DUNE_API_KEY
    }
    try:
        response = requests.post(dune_upload_url, headers=headers, data=payload)
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
    csv_writer.writerows(rows)
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
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ant-table-tbody'))
        )
        logging.info("Table loaded")
        
        # Wait for the table to be populated
        time.sleep(5)
        
        table = driver.find_element(By.CLASS_NAME, 'ant-table-tbody')
        rows = table.find_elements(By.TAG_NAME, 'tr')
        headers = [header.text for header in driver.find_element(By.CLASS_NAME, 'ant-table-thead').find_elements(By.TAG_NAME, 'th')]
        data_rows = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            data = [cell.text for cell in cells]
            if any(data):  # Only append non-empty rows
                data_rows.append(data)
        
        if not data_rows:
            logging.warning("No data found in the table")
        
        return headers, data_rows
    except TimeoutException:
        logging.error("Timeout while waiting for table to load")
        return [], []

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("WebDriver initialized successfully")
        driver.get('https://www.coinglass.com/bitcoin-etf')
        logging.info("Page loaded")
        
        click_flows_tab(driver)
        headers, data_rows = get_table_data(driver)
        
        if not data_rows:
            logging.error("No data retrieved, exiting")
            return
        
        # Convert to CSV
        csv_data = convert_to_csv(headers, data_rows)
        
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
