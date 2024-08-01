
import os
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time
from bs4 import BeautifulSoup

# Define the path
path_to_file = r"C:/Users/ACER/OneDrive/Desktop/web_scraper/"

# Ensure the directory exists
if not os.path.exists(path_to_file):
    os.makedirs(path_to_file)

mode = "scrape"  # mode=extract/scrape/""

def get_chrome_version():
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
    version, type = winreg.QueryValueEx(key, "version")
    return version

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-ssl-errors=yes')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-software-rasterizer')
    
    try:
        chrome_version = get_chrome_version()
        service = Service(ChromeDriverManager(version=chrome_version).install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error setting up ChromeDriver: {e}")
        print("Attempting to use system Chrome installation...")
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Failed to initialize Chrome: {e}")
            return None
    return driver

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
            
            # Wait for the menu items to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "sc-1s0saks-10"))
            )
            actions = ActionChains(driver)
            last_height = 0
            while True:
                # Locate all "Read more" buttons
                read_more_buttons = driver.find_elements(By.CSS_SELECTOR, ".sc-ya2zuu-0.SWRrQ")
                
                # Scroll through the buttons and click them
                for button in read_more_buttons:
                    try:
                        # Click the button
                        actions.move_to_element(button).click().perform()
                        time.sleep(3)  # Wait for the click action to complete

                    except Exception as e:
                        print(f"Failed to click 'Read more' button: {e}")
                
                # Scroll down by a smaller increment
                driver.execute_script('window.scrollBy(0, 1000)')
                time.sleep(2)  # Wait for the new content to load

                # Calculate new scroll height and compare with last scroll height
                new_height = driver.execute_script("return document.body.scrollHeight")
                print(f"New height: {new_height}, Last height: {last_height}")

                # Check if we've reached the end of the page
                if new_height == last_height:
                    break
                else:
                    last_height = new_height
            
            page_source = driver.page_source
            
            file_name = url.split('/')[-2] if '/' in url else 'default'
            with open(os.path.join(path_to_file, f"source_{file_name}.txt"), "w", encoding="utf-8") as f:
                f.write(page_source)
        
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return []
        
        finally:
            driver.quit()
    
    data = []
    file_name = url.split('/')[-2] if '/' in url else 'default'
    try:
        with open(os.path.join(path_to_file, f"source_{file_name}.txt"), "r", encoding="utf-8") as f:
            page_source = f.read()
            print(f"Successfully read source file for {url}. Length: {len(page_source)} characters")
    except Exception as e:
        print(f"Error reading source file for {url}: {e}")
        return []

    soup = BeautifulSoup(page_source, features="lxml")

    for item in soup.find_all("div", class_="sc-1s0saks-10 cYSFTJ"):
        title = soup.find('h1',class_='sc-7kepeu-0 sc-iSDuPN fwzNdh')
        item_out = {}
        item_out['title'] = title.text
        # item_out['Restaurant URL'] = url
        
        
        
        dish = item.find("h4", class_="sc-1s0saks-15 iSmBPS")
        item_out['Dish'] = dish.text if dish else None
        
        rating = item.find_all('i', class_="sc-rbbb40-1 iFnyeo sc-z30xqq-0 fehnhH")
        if len(rating) > 0:
            rating_num = 0
            for r in rating:
                if r.get('color') == '#F3C117':
                    rating_num += 1
            point_value = item.find_all('stop')
            if point_value != []:
                sec = point_value[1]
                value = sec.get('offset')
                decimal_value = float(value.strip('%'))/100
                rating_new = rating_num + decimal_value
                item_out['Rating'] = rating_new
        
        description = item.find("p", class_="sc-1s0saks-12 hcROsL")
        item_out['Description'] = description.text if description else None
        
        price = item.find("span", class_="sc-17hyc2s-1 cCiQWA")
        item_out['Price'] = price.text if price else None
        
        data.append(item_out)
    
    print(f"Extracted {len(data)} items from {url}")
    return data

# Read URLs from CSV file
urls = []
csv_path = os.path.join(path_to_file, 'file.csv')
with open(csv_path, 'r') as file:
    csv_reader = csv.reader(file)
    for row in csv_reader:
        if row:
            urls.append(row[0].strip())

print(f"Read {len(urls)} URLs from {csv_path}")

# Process each URL
print(urls)
all_data = []
for url in urls:
    url_data = process_url(url)
    all_data.extend(url_data)
    print(f"Total items collected so far: {len(all_data)}")

# Create DataFrame and save to CSV
df = pd.DataFrame(all_data)
output_file = os.path.join(path_to_file, "all_restaurants_data.csv")
df.to_csv(output_file, sep=";", index=False)

print(f"Script executed successfully. Data saved to {output_file}")
print(f"Total items collected: {len(all_data)}")