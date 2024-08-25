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

def upload_to_dune(csv_data):
    dune_upload_url = "https://api.dune.com/api/v1/table/upload/csv"
    payload = {
        "table_name": "btc_etf_flow",
        "description": "BTC ETF Flow Data",
        "is_private": False
    }
    files = {
        'data': ('btc_etf_flow.csv', csv_data, 'text/csv')
    }
    headers = {
        'X-DUNE-API-KEY': 'p0RZJpTPCUn9Cn7UTXEWDhalc53QzZXV'
    }
    try:
        response = requests.post(dune_upload_url, headers=headers, data=payload, files=files)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        logging.info(f"Dune API Response: {response.text}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error uploading to Dune: {str(e)}")
        return None

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
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("WebDriver initialized successfully")
        driver.get('https://www.coinglass.com/bitcoin-etf')
        logging.info("Page loaded")
        
        click_flows_tab(driver)
        headers, data_rows = get_table_data(driver)
        csv_data = convert_to_csv(headers, data_rows)
        
        print(csv_data)  # For debugging, you might want to remove this in production
        
        result = upload_to_dune(csv_data)
        if result:
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
