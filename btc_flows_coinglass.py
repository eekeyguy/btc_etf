import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

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

# Open a CSV file to write the data
with open('flows_usd_data.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    # Extract table headers
    headers = driver.find_element(By.CLASS_NAME, 'ant-table-thead').find_elements(By.TAG_NAME, 'th')
    header_row = [header.text for header in headers]
    writer.writerow(header_row)  # Write headers to the CSV file
    
    # Iterate through rows and extract data
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, 'td')
        data = [cell.text for cell in cells]  # Extract the text from each cell
        writer.writerow(data)  # Write the row data to the CSV file

# Close the browser
driver.quit()

print("Data has been written to 'flows_usd_data.csv'.")
