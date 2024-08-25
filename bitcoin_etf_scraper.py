import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import cloudscraper

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

def main():
    html_content = scrape_with_cloudscraper()
    
    if html_content:
        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', class_='etf')
        
        if table:
            headers = [th.text.strip() for th in table.find_all('th')]
            rows = []
            for tr in table.find_all('tr')[1:]:
                row = [td.text.strip() for td in tr.find_all('td')]
                if row:
                    rows.append(row)
            
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bitcoin_etf_flow_data_{current_time}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(rows)
            
            print(f"Data has been scraped and saved to {filename}")
        else:
            print("Table with class 'etf' not found on the page.")
    else:
        print("Failed to retrieve the webpage after multiple attempts.")

if __name__ == "__main__":
    main()
