
import os
import csv
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.core.utils import read_version_from_cmd 
from webdriver_manager.core.os_manager import PATTERN
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import subprocess
import pandas as pd
import time
from bs4 import BeautifulSoup
# Define the path
path_to_file = r"/home/shubh/zomato_scraper"

# Ensure the directory exists
if not os.path.exists(path_to_file):
    os.makedirs(path_to_file)

mode = "scrape"  # mode=extract/scrape/""



def setup_driver():
    chrome_options = webdriver.FirefoxOptions()
    chrome_options.add_argument('--no-sandbox')
    #chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.binary_location = "/usr/bin/firefox"  # Specify Chromium binary path
    
    print("Setting up FoxDriver...")
    try:
        #chrome_version = get_chrome_version()
        #service = ChromeService(ChromeDriverManager().install())
        #service = webdriver.ChromeService()
        #driver = webdriver.Chrome(service=service,options=chrome_options) #service=service, options=chrome_options
        version = read_version_from_cmd("/usr/bin/firefox-bin --version", PATTERN["firefox"])
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager(version=version).install()),options=chrome_options)
        print("FirefoxDriver setup successful")
        return driver
    except Exception as e:
        print(f"Error setting up FoxDriver: {e}")
        return None
    

def process_url(url):
    if not url.startswith('http'):
        url = f"https://www.zomato.com{url}"
    
    print(f"Processing URL: {url}")
    
    if mode != "extract":
        driver = setup_driver()
        if driver is None:
            print(f"Skipping URL due to driver initialization failure: {url}")
            return []
        
        try:
            driver.maximize_window()
            driver.get(url)
            
            
            xpath = "//div[contains(text(),'Show more')]"
            script = """
            var xpath = arguments[0];
            var matchingElement = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (matchingElement) {
                matchingElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',   
                    inline: 'nearest'
                });
                matchingElement.click();
            }
            """
            driver.execute_script(script, xpath)
            time.sleep(3)
            
            page_source = driver.page_source
            
            file_name = url.split('/')[-2] if '/' in url else 'default'
            with open(os.path.join(path_to_file, f"source_{file_name}.txt"), "w", encoding="utf-8") as f:
                f.write(page_source)
        
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return []
        
        finally:
            driver.quit()
    

def main():
    process_url('https://www.swiggy.com/offers-near-me')

main()