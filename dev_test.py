
import os
from urllib.parse import urlparse
import csv
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
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

# Use the current working directory for file paths
current_dir = os.getcwd()
print(current_dir)

mode = "scrape"  # mode=extract/scrape/""

def get_chrome_version():
    try:
        # Run the command to get the Chrome version
        result = subprocess.run(['google-chrome', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Decode the output to get the version string
        version = result.stdout.decode('utf-8').strip()
        return version
    except Exception as e:
        return str(e)

def setup_driver():
    chrome_options = webdriver.FirefoxOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.binary_location = "/usr/bin/firefox"  # Specify Chromium binary path
    
    print("Setting up FoxDriver...")
    try:
        version = read_version_from_cmd("/usr/bin/firefox-bin --version", PATTERN["firefox"])
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager(version=version).install()), options=chrome_options)
        print("FirefoxDriver setup successful")
        return driver
    except Exception as e:
        print(f"Error setting up FoxDriver: {e}")
        return None

def process_url(url):
    print(f"Processing URL: {url}")
    
    if mode != "extract":
        driver = setup_driver()
        if driver is None:
            print(f"Skipping URL due to driver initialization failure: {url}")
            return []
        
        try:
            driver.maximize_window()
            driver.get(url)
            print('Driver started')
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight-1500)")
            print('First element found')
            
            xpath = "//div[contains(text(),'see more')]"
            script = """
            var xpath = arguments[0];
            var matchingElement = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (matchingElement) {
                matchingElement.click();
            }
            """
            driver.execute_script(script, xpath)
            time.sleep(3)
            
            page_source = driver.page_source
            with open(os.path.join(current_dir, "source.txt"), "w+") as f:
                f.write(page_source)
        
        except Exception as e:
            print(f"Error processing URL {url} while writing: {e}")
            return []
        
        finally:
            driver.quit()
    
    data = []
    try:
        with open(os.path.join(current_dir, "source.txt"), "r") as f:
            page_source = f.read()
            print(f"Successfully read source file for {url}. Length: {len(page_source)} characters")
    except Exception as e:
        print(f"Error reading source file for {url}: {e}")
        return []

    soup = BeautifulSoup(page_source, features="lxml")

    main_div = soup.find_all('div', class_='sc-bke1zw-0 fIuLDK')
    main_div = main_div[0]
    
    link_div = main_div.find_all("a")
    
    for a in link_div:
        item_out = {}
        link = a['href']
        name = a.find('h5').text
        num_places = a.find('p').text
        item_out['link'] = link
        item_out['name'] = name
        item_out['num_places'] = num_places
        
        data.append(item_out)

    print(f"Extracted {len(data)} items from {url}")
    return data

def process_locality(url):
    driver = setup_driver()
    if driver is None:
        print(f"Skipping URL due to driver initialization failure: {url}")
        return []
    
    try:
        driver.maximize_window()
        driver.get(url)
        print('Driver started')
        time.sleep(1)
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            time.sleep(1)
            driver.execute_script("window.scrollBy(0,1500)")
            time.sleep(2)  # Wait for new content to load
            
            print(last_height)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        page_source = driver.page_source
        print("page data extracted successfully")
        with open(os.path.join(current_dir, "temp.txt"), "w+") as f:
            f.write(page_source)
    
    except Exception as e:
        print(f"Error processing URL {url} while writing: {e}")
        return []
    
    finally:
        driver.quit()
    
    data = []
    try:
        with open(os.path.join(current_dir, "temp.txt"), "r") as f:
            page_source = f.read()
            print(f"Successfully read source file for {url}. Length: {len(page_source)} characters")
    except Exception as e:
        print(f"Error reading source file for {url} : {e}")
        return []

    soup = BeautifulSoup(page_source, features="lxml")
    
    main_div = soup.find_all('a', class_='sc-gLdKKF kSLcCi')
    print("all a tag collected")
    print(main_div)
    
    for a in main_div:
        print(a)
        item_out = {}
        link = a['href']
        print(link)
        item_out['link'] = link
        data.append(item_out)

    print(f"Extracted {len(data)} items from {url}")

    return data

def complete_process(city_name):
    root_url = "https://www.zomato.com"
    full_url = f"{root_url}/{city_name.lower()}"
    print(f"Full URL constructed: {full_url}")
    
    data = process_url(full_url)
    df = pd.DataFrame(data)
    output_file = os.path.join(current_dir, "localitylinks.csv")
    df.to_csv(output_file, sep=";", index=False)

    print(f"Script executed successfully. Data saved to {output_file}")
    print(f"Total items collected: {len(data)}")

    print("now finding links of resturents in all localites")
    
    df_locality = pd.read_csv(os.path.join(current_dir, "localitylinks.csv"), sep=";")
    col_list = df_locality['link'].tolist()

    data = []
    for local in col_list:
        print(local)
        data1 = process_locality(local)
        data.extend(data1)
        
    print("everything went sucessfull")

    resto_link_locality = pd.DataFrame(data)
    output_file = os.path.join(current_dir, "locality_resto_links.csv")
    resto_link_locality.to_csv(output_file, sep=";", index=False)

    df_locality_temp = pd.read_csv(os.path.join(current_dir, "locality_resto_links.csv"), sep=";")
    col_list = df_locality_temp['link'].tolist()

    print(len(col_list))
    temp_test = set(col_list)
    unique_resto = list(temp_test)
    print(len(unique_resto))

    dp_final = pd.DataFrame(unique_resto)

    output_file2 = os.path.join(current_dir, "uique_resto.csv")
    dp_final.to_csv(output_file2, sep=";", index=False)
    print("all_resto_links are saved at ",output_file2)
    return output_file2
