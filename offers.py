
import os
import csv
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.core.utils import read_version_from_cmd 
from webdriver_manager.core.os_manager import PATTERN
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException,NoSuchElementException
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
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument('--no-sandbox')
    firefox_options.add_argument('--headless')
    firefox_options.add_argument('--disable-dev-shm-usage')
    firefox_options.add_argument('--ignore-ssl-errors=yes')
    firefox_options.add_argument('--ignore-certificate-errors')
    firefox_options.add_argument('--disable-gpu')
    firefox_options.add_argument('--disable-extensions')
    firefox_options.add_argument('--disable-software-rasterizer')
    firefox_options.binary_location = "/usr/bin/firefox"  # Specify Chromium binary path
    
    print("Setting up FoxDriver...")
    try:
        version = read_version_from_cmd("/usr/bin/firefox-bin --version", PATTERN["firefox"])
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager(version=version).install()), options=firefox_options)
        print("FirefoxDriver setup successful")
        return driver
    except Exception as e:
        print(f"Error setting up FoxDriver: {e}")
        return None    
    

def extract_offers(driver, url):
    temp_offers = []
    try:
        driver.get(url)
        
        # Try to find and modify the "row" element
        try:
            element = driver.find_element(By.CLASS_NAME, "row")
            driver.execute_script("arguments[0].classList.remove('row');", element)
        except Exception as e:
            print(f"Error finding or modifying 'row' element: {e}")
            # Continue execution even if this fails
        
        # Try to find and process offer elements
        try:
            title = driver.execute_script("return document.querySelector('.sc-aXZVg.cNRZhA')")
            elements = driver.execute_script("return document.querySelectorAll('.sc-hHOBiw.hKJHKQ');")
            for idx, element in enumerate(elements):
                print(idx)
                try:
                    element.click()
                    
                    # Wait for the text element to be visible and log its text
                    text_elem = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, '.sc-aXZVg.cKDIFf.sc-eNSrOW.htXejL'))
                    )
                    temp = {}
                    temp['Restaurant'] = title.text
                    temp['Offers']=text_elem.text
                    temp_offers.append(temp)
                    
                    close_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.sc-dtInlm.caGqNi'))
                    )
                    close_button.click()
                    print('modal closed')
                    time.sleep(3)
                except Exception as e:
                    print(f"Error processing offer {idx}: {e}")
                    # Continue to next offer even if this one fails
        except Exception as e:
            print(f"Error finding offer elements in {url}: {e}")
    
    except Exception as e:
        print(f"An unexpected error occurred in {url}: {e}")
    
    if not temp_offers:
        print('No offers found')
    
    return temp_offers

def process_url(url):
    # if not url.startswith('http'):
    #     url = f"https://www.zomato.com{url}"
    
    print(f"Processing URL: {url}")
    
    if mode != "extract":
        driver = setup_driver()
        if driver is None:
            print(f"Skipping URL due to driver initialization failure: {url}")
            return []
        
        driver.get(url)
        driver.maximize_window()
        WebDriverWait(driver,30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "jXGZuP"))
        )
        try:
            select_offer_script = """q= document.querySelectorAll('.sc-cmfmEs.hYhXhj');q[4].scrollIntoView({behavior: 'smooth',block: 'center',inline: 'center'});q[4].click();"""
            driver.execute_script(select_offer_script)
            t1 = time.time()
            while True:
                try:
                    show_more_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".InfoCard__Container-sc-16vtyhn-0.fBowAU"))
                    )
                    
                    # Take a screenshot
                    #driver.save_screenshot('shot.png')
                    
                    # Scroll into view and click the button
                    driver.execute_script("arguments[0].scrollIntoView();", show_more_button)
                    driver.execute_script("arguments[0].click();", show_more_button)
                    print('button clicked')
                    # Wait for a few seconds for the page to load more content
                    time.sleep(3)
                    
                    if time.time()-t1 > 1:
                        break
                    
                except TimeoutException:
                    print('No more "show more" buttons found, exiting loop.')
                    break

                    
            page_source = driver.page_source    
            with open('check.txt','w+') as f:
                f.write(page_source)
            print('Source saved')
            soup = BeautifulSoup(page_source,features='lxml')
            grid = soup.find('div',class_='sc-gLLvby jXGZuP')
            a_tags = grid.find_all('a')
            fp =  open('offer_links.txt','a+')
            for tag in a_tags:
                print(tag['href'])
                fp.write(f"{tag['href']}\n")
            print('Prospect done')
            fp.close()
            urls = []
            with open('offer_links.txt','r') as offer_file:
                csv_reader = csv.reader(offer_file)
                for row in csv_reader:
                    if row:
                        urls.append(row[0].strip())
            offer_list = []
            for url in urls:
                data = extract_offers(driver,url)
                offer_list.extend(data)
            
            
            df = pd.DataFrame(offer_list)
            df.to_csv('offers.txt',mode='a',sep=';',index=False)
            
        
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return []
        
        finally:
            driver.quit()
    

def main():
    process_url('https://www.swiggy.com/city/lucknow')
    # driver = setup_driver()
    # data = extract_offers(driver,'https://www.swiggy.com/restaurants/craving-o-clock-2nd-stage-btm-layout-bangalore-362852')
    # print(data)
    

    
    

main()