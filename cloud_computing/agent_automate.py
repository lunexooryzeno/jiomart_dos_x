from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import traceback
import os
from pathlib import Path
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

import sys
import json
import requests
import time
# Basic Chrome options
options = Options()



BASE_URL = "https://nexonotp.in"
# BASE_URL = "http://127.0.0.1:4080"
## ---------------------------------------------------- ##
# Variables
## ---------------------------------------------------- ##


def read_file_data():
    url = f"{BASE_URL}/autonomous/agent/configuration"
    response = requests.get(url)
    return response.json()

data = read_file_data()
folder_path = data.get("slotPath")
coupon_code = data.get("coupon_to_apply")
cart_items  = data.get("cart_items")

what_is_the_jiomart_order_limit = 1

store_code = "F1ZP"

overwrite = False

use_proxy = True

mitmdump_port = "8753"
PROXY = "127.0.0.1:" + mitmdump_port


# mitmdump -s intercept_requests.py -p 8753
## ---------------------------------------------------- ##



## ---------------------------------------------------- ##
# Functions

def get_cart_id(specific_headers):
    url = "https://www.jiomart.com/mst/rest/v1/5/cart/get"
    
    # Headers
    headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            'authtoken': specific_headers.get("localStorage").get("authtoken"),
            "pin": specific_headers.get("localStorage").get("nms_mgo_pincode"),
            "priority": "u=0, i",
            "referer": "https://www.jiomart.com",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "storecode": store_code,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            'userid': specific_headers.get("localStorage").get("userid"),
            "x-requested-with": "XMLHttpRequest"
        }

    # Cookies
    cookies = {
            '_ALGOLIA': specific_headers.get("cookies").get("_ALGOLIA"),
            '_fbp': specific_headers.get("cookies").get("_fbp"),
            'WZRK_G': specific_headers.get("cookies").get("WZRK_G"),
            '_gcl_au': specific_headers.get("cookies").get("_gcl_au"),
            'new_customer': 'true',
            'ajs_anonymous_id': specific_headers.get("localStorage").get("ajs_anonymous_id"),
            'nms_mgo_city': specific_headers.get("localStorage").get("nms_mgo_city"),
            'nms_mgo_state_code': specific_headers.get("localStorage").get("nms_mgo_state_code"),
            'AKA_A2': specific_headers.get("cookies").get("AKA_A2"),
            '_gid': specific_headers.get("cookies").get("_gid"),
            'nms_mgo_pincode': specific_headers.get("localStorage").get("nms_mgo_pincode"),
            '_gat': '1',
            '_ga_XHR9Q2M3VV': specific_headers.get("cookies").get("_ga_XHR9Q2M3VV"),
            '_ga': specific_headers.get("cookies").get("_ga"),
            'RT': specific_headers.get("cookies").get("RT"),
            'WZRK_S_88R-W4Z-495Z': '%7B%22p%22%3A12%2C%22s%22%3A1755119641%2C%22t%22%3A1755119764%7D'
        }

    try:
        # Make the GET request
        response = requests.get(url, headers=headers, cookies=cookies)
        
        # Try to parse the response
        try:
            response_data = response.json()
            if response_data.get('status') == 'success':
                return response_data.get('result').get('cart').get('id')
            else:
                return False
        except json.JSONDecodeError:
            print("Warning: Could not parse response as JSON")
            return False
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

def get_cart_data(specific_headers):
    url = "https://www.jiomart.com/mst/rest/v1/5/cart/get"
    
    # Headers
    headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            'authtoken': specific_headers.get("localStorage").get("authtoken"),
            "pin": specific_headers.get("localStorage").get("nms_mgo_pincode"),
            "priority": "u=0, i",
            "referer": "https://www.jiomart.com",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "storecode": store_code,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            'userid': specific_headers.get("localStorage").get("userid"),
            "x-requested-with": "XMLHttpRequest"
        }

    # Cookies
    cookies = {
            '_ALGOLIA': specific_headers.get("cookies").get("_ALGOLIA"),
            '_fbp': specific_headers.get("cookies").get("_fbp"),
            'WZRK_G': specific_headers.get("cookies").get("WZRK_G"),
            '_gcl_au': specific_headers.get("cookies").get("_gcl_au"),
            'new_customer': 'true',
            'ajs_anonymous_id': specific_headers.get("localStorage").get("ajs_anonymous_id"),
            'nms_mgo_city': specific_headers.get("localStorage").get("nms_mgo_city"),
            'nms_mgo_state_code': specific_headers.get("localStorage").get("nms_mgo_state_code"),
            'AKA_A2': specific_headers.get("cookies").get("AKA_A2"),
            '_gid': specific_headers.get("cookies").get("_gid"),
            'nms_mgo_pincode': specific_headers.get("localStorage").get("nms_mgo_pincode"),
            '_gat': '1',
            '_ga_XHR9Q2M3VV': specific_headers.get("cookies").get("_ga_XHR9Q2M3VV"),
            '_ga': specific_headers.get("cookies").get("_ga"),
            'RT': specific_headers.get("cookies").get("RT"),
            'WZRK_S_88R-W4Z-495Z': '%7B%22p%22%3A12%2C%22s%22%3A1755119641%2C%22t%22%3A1755119764%7D'
        }

    try:
        # Make the GET request
        response = requests.get(url, headers=headers, cookies=cookies)
        
        # Try to parse the response
        try:
            response_data = response.json()
            if response_data.get('status') == 'success':
                return response_data
            else:
                return False
        except json.JSONDecodeError:
            print("Warning: Could not parse response as JSON")
            return False
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

def apply_coupon(coupon_code, specific_headers):
    url = "https://www.jiomart.com/mst/rest/v1/5/cart/apply_coupon"
    params = {
        "coupon_code": coupon_code,
        "cart_id": get_cart_id(specific_headers)
    }
    

    # Headers
    headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            'authtoken': specific_headers.get("localStorage").get("authtoken"),
            "pin": specific_headers.get("localStorage").get("nms_mgo_pincode"),
            "priority": "u=0, i",
            "referer": "https://www.jiomart.com",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "storecode": store_code,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            'userid': specific_headers.get("localStorage").get("userid"),
            "x-requested-with": "XMLHttpRequest"
        }

    # Cookies
    cookies = {
            '_ALGOLIA': specific_headers.get("cookies").get("_ALGOLIA"),
            '_fbp': specific_headers.get("cookies").get("_fbp"),
            'WZRK_G': specific_headers.get("cookies").get("WZRK_G"),
            '_gcl_au': specific_headers.get("cookies").get("_gcl_au"),
            'new_customer': 'true',
            'ajs_anonymous_id': specific_headers.get("localStorage").get("ajs_anonymous_id"),
            'nms_mgo_city': specific_headers.get("localStorage").get("nms_mgo_city"),
            'nms_mgo_state_code': specific_headers.get("localStorage").get("nms_mgo_state_code"),
            'AKA_A2': specific_headers.get("cookies").get("AKA_A2"),
            '_gid': specific_headers.get("cookies").get("_gid"),
            'nms_mgo_pincode': specific_headers.get("localStorage").get("nms_mgo_pincode"),
            '_gat': '1',
            '_ga_XHR9Q2M3VV': specific_headers.get("cookies").get("_ga_XHR9Q2M3VV"),
            '_ga': specific_headers.get("cookies").get("_ga"),
            'RT': specific_headers.get("cookies").get("RT"),
            'WZRK_S_88R-W4Z-495Z': '%7B%22p%22%3A12%2C%22s%22%3A1755119641%2C%22t%22%3A1755119764%7D'
        }

    try:
        # Make the GET request
        response = requests.get(url, params=params, headers=headers, cookies=cookies)
        
        # Try to parse the response
        try:
            response_data = response.json()
            if response_data.get('status') == 'success':
                return True
            else:
                return False
        except json.JSONDecodeError:
            print("Warning: Could not parse response as JSON")
            return False
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def unapply_coupon(coupon_code, specific_headers):
    url = f"https://www.jiomart.com/mst/rest/v1/5/cart/unapply_coupon"
    params = {
        "coupon_code": coupon_code,
        "cart_id": get_cart_id(specific_headers)
    }
    
    # Headers
    headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            'authtoken': specific_headers.get("localStorage").get("authtoken"),
            "pin": specific_headers.get("localStorage").get("nms_mgo_pincode"),
            "priority": "u=0, i",
            "referer": "https://www.jiomart.com",
            "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "storecode": store_code,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
            'userid': specific_headers.get("localStorage").get("userid"),
            "x-requested-with": "XMLHttpRequest"
        }

    # Cookies
    cookies = {
            '_ALGOLIA': specific_headers.get("cookies").get("_ALGOLIA"),
            '_fbp': specific_headers.get("cookies").get("_fbp"),
            'WZRK_G': specific_headers.get("cookies").get("WZRK_G"),
            '_gcl_au': specific_headers.get("cookies").get("_gcl_au"),
            'new_customer': 'true',
            'ajs_anonymous_id': specific_headers.get("localStorage").get("ajs_anonymous_id"),
            'nms_mgo_city': specific_headers.get("localStorage").get("nms_mgo_city"),
            'nms_mgo_state_code': specific_headers.get("localStorage").get("nms_mgo_state_code"),
            'AKA_A2': specific_headers.get("cookies").get("AKA_A2"),
            '_gid': specific_headers.get("cookies").get("_gid"),
            'nms_mgo_pincode': specific_headers.get("localStorage").get("nms_mgo_pincode"),
            '_gat': '1',
            '_ga_XHR9Q2M3VV': specific_headers.get("cookies").get("_ga_XHR9Q2M3VV"),
            '_ga': specific_headers.get("cookies").get("_ga"),
            'RT': specific_headers.get("cookies").get("RT"),
            'WZRK_S_88R-W4Z-495Z': '%7B%22p%22%3A12%2C%22s%22%3A1755119641%2C%22t%22%3A1755119764%7D'
        }

    try:
        # Make the GET request
        response = requests.get(url, params=params, headers=headers, cookies=cookies)
        
        # Try to parse the response
        try:
            response_data = response.json()
            if response_data.get('status') == 'success':
                return True
            else:
                return False
        except json.JSONDecodeError:
            print("Warning: Could not parse response as JSON")
            return False
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def remove_all_items_from_cart(specific_headers):
    
    while True:
        # Headers
        headers = {
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-encoding": "gzip, deflate, br, zstd",
                "accept-language": "en-US,en;q=0.9",
                'authtoken': specific_headers.get("localStorage").get("authtoken"),
                "pin": specific_headers.get("localStorage").get("nms_mgo_pincode"),
                "priority": "u=0, i",
                "referer": "https://www.jiomart.com",
                "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "storecode": store_code,
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
                'userid': specific_headers.get("localStorage").get("userid"),
                "x-requested-with": "XMLHttpRequest"
            }
        
        data = get_cart_data(specific_headers).get("result").get("cart").get("lines")
        
        if len(data) == 0:
            break
        else:
            for products in data:
                
                product_code = products.get("product_code")
                quantity = products.get("qty")
                    
                # Base URL
                url = "https://www.jiomart.com/mst/rest/v1/5/cart/remove_item"
                
                # Query parameters
                params = {
                    "product_code": str(product_code),
                    "qty": str(quantity)
                }
                
                try:
                    # Make the GET request
                    response = requests.get(url, params=params, headers=headers)
                    
                    # Try to parse the response
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError:
                        return False
                    
                except Exception as e:
                    return False

    return True


def add_item_with_retry(item_code, item_qty, headers, pincode, store_code, item_name_optional=None, retries=2):
    """
    Attempts to add an item to the cart with optional retries.

    Args:
        item_code (int): Item code.
        item_qty (int): Quantity to add.
        headers (dict): Request headers.
        pincode (str): Delivery pincode.
        store_code (str): Store code.
        item_name_optional (str, optional): Optional item name for logging.
        retries (int): Number of total attempts (default 2).

    Returns:
        bool: True if item added successfully, False otherwise.
    """
    for attempt in range(1, retries + 1):
        success = add_item(item_code, item_qty, headers, pincode, store_code)
        if success:
            print(f"Product successfully added! {item_name_optional or ''}")
            return True
        else:
            if attempt < retries:
                print(f"Product not added. Retrying... ({attempt}/{retries})")
            else:
                print(f"Product not added after {retries} attempts! {item_name_optional or ''}")
    return False



## ---------------------------------------------------- ##

def append_unique_profile(text, profile_name):
    url = f"{BASE_URL}/shipments/set/pending_shipments"
    payload = {"text": text, "profile_name": profile_name}
    response = requests.get(url, json=payload)
    return response.json()["result"]



def add_item(product_code, quantity, specific_headers, pincode, storecode):
    # Base URL
    url = "https://www.jiomart.com/mst/rest/v1/5/cart/add_item"
    
    # Query parameters
    params = {
        "product_code": product_code,
        "qty": quantity,
        "seller_id": "1",
        "n": str(int(time.time() * 1000))  # Current timestamp in milliseconds
    }
    
    # Headers
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        'authtoken': specific_headers.get("localStorage").get("authtoken"),
        "pin": pincode,
        "priority": "u=0, i",
        "referer": "https://www.jiomart.com",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "storecode": storecode,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        'userid': specific_headers.get("localStorage").get("userid"),
        "x-requested-with": "XMLHttpRequest"
    }
    
    # Cookies
    cookies = {
        '_ALGOLIA': specific_headers.get("cookies").get("_ALGOLIA"),
        '_fbp': specific_headers.get("cookies").get("_fbp"),
        'WZRK_G': specific_headers.get("cookies").get("WZRK_G"),
        '_gcl_au': specific_headers.get("cookies").get("_gcl_au"),
        'new_customer': 'true',
        'ajs_anonymous_id': specific_headers.get("localStorage").get("ajs_anonymous_id"),
        'nms_mgo_city': specific_headers.get("localStorage").get("nms_mgo_city"),
        'nms_mgo_state_code': specific_headers.get("localStorage").get("nms_mgo_state_code"),
        'AKA_A2': specific_headers.get("cookies").get("AKA_A2"),
        '_gid': specific_headers.get("cookies").get("_gid"),
        'nms_mgo_pincode': specific_headers.get("localStorage").get("nms_mgo_pincode"),
        '_gat': '1',
        '_ga_XHR9Q2M3VV': specific_headers.get("cookies").get("_ga_XHR9Q2M3VV"),
        '_ga': specific_headers.get("cookies").get("_ga"),
        'RT': specific_headers.get("cookies").get("RT"),
        'WZRK_S_88R-W4Z-495Z': '%7B%22p%22%3A12%2C%22s%22%3A1755119641%2C%22t%22%3A1755119764%7D'
    }
    
    try:
        # Make the GET request
        response = requests.get(url, params=params, headers=headers, cookies=cookies)
        
        print(response.content)
        
        # Try to parse the response
        try:
            response_data = response.json()
            
            if response_data.get('status') == 'success':
                return True
            else:
                print(f"Warning: {response_data}")
                return False
        except json.JSONDecodeError:
            print("Warning: Could not parse response as JSON")
            return False
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False



def wait_and_click_placeorder(driver, timeout=30):
    selector = (By.CSS_SELECTOR, "button[name='placeorder']")
    wait = WebDriverWait(driver, timeout)

    end = time.time() + timeout
    
    while time.time() < end:
        try:
            # Ensure visible
            btn = wait.until(EC.visibility_of_element_located(selector))

            # Ensure enabled
            if not btn.is_enabled():
                time.sleep(0.5)
                continue

            try:
                btn.click()
                return "place_order_clicked"

            except ElementClickInterceptedException:
                # overlay or something on top → wait and retry
                time.sleep(0.5)
                continue

        except TimeoutException:
            pass

        time.sleep(0.3)

    return "place_order_timeout"


def automate(specific_headers, profile_path, profile_name):
    account_credentials_data = read_json(profile_path)["data"]
    original_profile_path = profile_path
    profile_path = create_new_one_profile(os.getcwd() + "\\accounts")
    
    # (Optional) ignore certificate errors — useful if mitmproxy cert not imported
    options.add_argument("--ignore-certificate-errors")
    options.set_capability("acceptInsecureCerts", True)

    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument('--start-maximized')
    

    
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # set proxy server
    if use_proxy:
        options.add_argument(f"--proxy-server=http://{PROXY}")
    
    
    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"[ERROR] Failed to start Chrome for {profile_name}")
        return "chrome_start_error"
    
    load_storage(driver, account_credentials_data)
    time.sleep(4)
    
    
    
    try:
        driver.get("about:blank")

        # JS to set tab title and floating banner
        js_banner = f"""
            document.title = 'JioMart - {profile_name}';
            const banner = document.createElement('div');
            banner.innerText = '{profile_name}';
            banner.style.position = 'fixed';
            banner.style.top = '10px';
            banner.style.left = '10px';
            banner.style.padding = '8px 15px';
            banner.style.backgroundColor = '#222';
            banner.style.color = '#fff';
            banner.style.zIndex = '999999';
            banner.style.fontSize = '20px';
            banner.style.borderRadius = '8px';
            document.body.appendChild(banner);
        """
        driver.execute_script(js_banner)

        # Open remaining URLs in new tabs
        for url in ["https://www.jiomart.com/checkout/cart"]:
            driver.execute_script(f"window.open('{url}', '_blank');")

        # Apply banner script to each new tab
        for handle in driver.window_handles[1:]:
            driver.switch_to.window(handle)
            driver.execute_script(js_banner)
    except Exception as e:
        print(f"[ERROR] {profile_name} → {e}")
    
    
    
    for i in range(what_is_the_jiomart_order_limit):
        if what_is_the_jiomart_order_limit != 1 and i != 0:
            print(f"[INFO] {profile_name} → Starting cart clear attempt {i + 1} of {what_is_the_jiomart_order_limit}...")
            # Open new cart tab again
            driver.execute_script("window.open('https://www.jiomart.com/checkout/cart', '_blank');")

            # Apply banner again on the newly opened tab
            new_tab = driver.window_handles[-1]
            driver.switch_to.window(new_tab)
            driver.execute_script(js_banner)
            
        # Wait for the page to be fully loaded
        wait = WebDriverWait(driver, 40)  # Wait up to 20 seconds
        
        # Wait for the body element to be present, indicating the page has loaded
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # Wait for page to be fully loaded
        try:
            # Wait for page to be fully loaded
            WebDriverWait(driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except:
            return "timeout"
        
        try:
            # Wait up to 12 seconds until the text "Your Cart is Empty!" appears
            WebDriverWait(driver, 12).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, "div.j-text.emptycart-title.j-text-heading-xxs.ng-star-inserted"),
                    "Your Cart is Empty!"
                )
            )
            print("Cart is empty message appeared!")
        except:
            pass
            
        
        
        try:
            specific_headers = specific_headers[0]
            
            
            data = get_cart_data(specific_headers)
            if not data:
                print("Failed to retrieve cart data, possibly due to invalid headers or profile logged out.")
                return "failed_due_to_invalid_headers"
            
            if data.get("status") == "success":
                print("Cart data retrieved successfully !")
                if len(data["result"]["cart"]["lines"]) != 0:
                    print("Cart was not empty, proceeding to clear cart...")
                    if remove_all_items_from_cart(specific_headers):
                        print("Cart was not empty, but now cleared!")
                    else:
                        print("Failed to clear cart!")
                        return "failed_to_clear_cart"
            else:
                print("Failed to retrieve cart data.")
                return "failed_to_retrieve_cart_data"
            
            driver.refresh()
            
            empty_message_appeared = True
            
            try:
                # Wait for the body element to be present, indicating the page has loaded
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Wait up to 12 seconds until the text "Your Cart is Empty!" appears
                WebDriverWait(driver, 12).until(
                    EC.text_to_be_present_in_element(
                        (By.CSS_SELECTOR, "div.j-text.emptycart-title.j-text-heading-xxs.ng-star-inserted"),
                        "Your Cart is Empty!"
                    )
                )
                print("Cart is empty message appeared!")
                empty_message_appeared = True
            except:
                empty_message_appeared = False
                    
            if not empty_message_appeared:
                print("Failed to confirm cart is empty after multiple attempts.")
                return "failed_to_clear_cart"
            
            try:
                # Wait up to 20 seconds for the text to appear anywhere on the page
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(), \"Sign In\")]")
                    )
                )
                print("Profile Logout !")
                return "profile_logout"
            except:
                pass
                


            # Set Items In Cart
            for items in cart_items:
                if items.get("include_in_cart") == True:
                    add_item_with_retry(items.get("product_code"), items.get("quantity"), specific_headers, items.get("pincode"), items.get("store_code"), items.get("item_name_optional"))


            # Now try to apply coupon
            data = get_cart_data(specific_headers)
            if not data:
                print("Failed to retrieve cart data, possibly due to invalid headers or profile logged out.")
                return "failed_due_to_invalid_headers"
            
            if data.get("status") == "success":
                applied_coupon = data.get("result").get("cart").get("applied_coupons")
                if not applied_coupon:
                    if apply_coupon(coupon_code, specific_headers):
                        print(f"Coupon successfully applied! '{coupon_code}' directly.")
                    else:
                        print(f"Failed to apply coupon after all attempts! '{coupon_code}'.{profile_name}")
                        return "failed_to_apply_coupon"
                else:
                    print(f"Coupon already applied in cart: {applied_coupon}. {profile_name}")
                    if applied_coupon == coupon_code:
                        print(f"Target coupon '{coupon_code}' is already applied. No action needed. {profile_name}")
                    elif unapply_coupon(applied_coupon, specific_headers):
                        print("Let me unapply it first...")
                        print(f"Successfully unapplied existing coupon: {applied_coupon}. Now applying target coupon...")
                        time.sleep(1)
                        if apply_coupon(coupon_code, specific_headers):
                            print(f"Coupon successfully applied after unapplying old one! '{coupon_code}'. {profile_name}")
                        else:
                            print(f"Failed to apply coupon after unapplying old one! '{coupon_code}'. {profile_name}")
                            return "failed_to_apply_coupon"
                    else:
                        print(f"Failed to unapply existing coupon: {applied_coupon[0]}. {profile_name}")
                        return "failed_to_unapply_existing_coupon"
            else:
                print("Failed to retrieve cart data.")
                return "failed_to_retrieve_cart_data"
                
            
            
            driver.refresh()
            
            placed_button_response = wait_and_click_placeorder(driver, 30)
            
            if "jiomart.com/checkout/cart" in driver.current_url and placed_button_response == "place_order_timeout":
                try:
                    # Wait up to 20 seconds for the text to appear anywhere on the page
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//*[contains(text(), \"order limit. More great picks await tomorrow — See you soon.\")]")
                        )
                    )
                    print("You’ve reached today’s jiomart order limit")
                    
                    return "order_limit_exceeds"
                except:
                    return "something_went_wrong_in_cart_page"
            

            
            
            print("Clicked on place order")
            
            try:
                # Wait for page to be fully loaded
                WebDriverWait(driver, 30).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except:
                return "timeout"
                
            
            time.sleep(2)
            
            # Wait for the Make Payment button to be clickable and click it
            make_payment_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='button Make Payment']")))
            make_payment_button.click()
            
            print("Clicked on make payment")
            time.sleep(5)
            try:
                # Wait for page to be fully loaded
                WebDriverWait(driver, 30).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
            except:
                return "timeout"
                
            
            try:
                # Wait for page to be fully loaded
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Do you wish to continue with cash on delivery?')]"))
                )
            except:
                if "jiomart.com/checkout/cart" in driver.current_url:
                    print("Returned to cart page, something went wrong !")
                    try:
                        # Wait up to 20 seconds for the text to appear anywhere on the page
                        WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//*[contains(text(), \"order limit. More great picks await tomorrow — See you soon.\")]")
                            )
                        )
                        print("You’ve reached today’s jiomart order limit")
                        
                        return "order_limit_exceeds"
                    except:
                        return "something_went_wrong_in_payment_page"
                
                
            # Wait for the cash on delivery confirmation message to appear
            cod_message = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Do you wish to continue with cash on delivery?')]")))
            print("Cash on delivery message appeared")
            
            # Step 1: Scroll to bottom to make sure COD section is visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # wait for any lazy loading

            # Step 2: Wait until the Cash on Delivery button is clickable
            # Wait for and click the Cash on Delivery element using CSS class
            cod_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".css-9oimx6")))
            cod_element.click()
            time.sleep(1)
                    
            
            # Wait for the Proceed button to be clickable and click it
            try:
                # First, find all matching buttons to verify we have the correct one
                proceed_buttons = driver.find_elements(By.CSS_SELECTOR, "button.j-button.j-button-size__medium.primary[aria-label='Proceed']")
                if not proceed_buttons:
                    raise Exception("No Proceed button found")
                
                # Find the button that contains the text "Proceed"
                proceed_button = None
                for button in proceed_buttons:
                    if "Proceed" in button.text:
                        proceed_button = button
                        break
                
                if not proceed_button:
                    raise Exception("Could not find button with text 'Proceed'")
                    
                # Scroll the button into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", proceed_button)
                time.sleep(1)  # Wait for scroll to complete
                
                # Verify the button is visible and enabled
                if not proceed_button.is_displayed():
                    raise Exception("Proceed button is not visible")
                if not proceed_button.is_enabled():
                    raise Exception("Proceed button is not enabled")
                    
                # Try multiple click methods
                try:
                    # Method 1: Regular click
                    proceed_button.click()
                except Exception as e:
                    print(f"Regular click failed: {str(e)}")
                    try:
                        # Method 2: JavaScript click
                        driver.execute_script("arguments[0].click();", proceed_button)
                    except Exception as e:
                        print(f"JavaScript click failed: {str(e)}")
                        # Method 3: Actions click
                        from selenium.webdriver.common.action_chains import ActionChains
                        actions = ActionChains(driver)
                        actions.move_to_element(proceed_button).click().perform()
                
                print("Clicked on Proceed button")
                
                
                # --- Watch for redirect ---
                timeout = 8  # seconds to wait for potential redirect
                start_time = time.time()
                while time.time() - start_time < timeout:
                    current_url = driver.current_url
                    if "jiomart.com/checkout/success" in current_url:
                        print(f"Redirected to Jiomart: {current_url} -> Closing browser.")
                        break
                    time.sleep(0.5)  # check every 0.5s
                
                if what_is_the_jiomart_order_limit == 1:
                    driver.quit()
                    print(append_unique_profile(original_profile_path.replace("\\account_data.json", ""), profile_name))
                    return "order_placed_success"
                else:
                    print(append_unique_profile(original_profile_path.replace("\\account_data.json", ""), profile_name))
                
            except Exception as e:
                print(f"Failed to click Proceed button: {str(e)}")
                raise
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            traceback.print_exc()



def read_json(full_path):
    url = f"{BASE_URL}/shipments/pending/read"
    payload = {"path": full_path}
    response = requests.post(url, json=payload)
    return response.json()


def get_profile_info(profile_local_credentials_name):
    try:
        return read_json(profile_local_credentials_name)["data"]
    except:
        return None


def countdown(minutes):
    total_seconds = minutes * 60
    try:
        for remaining in range(total_seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            timer_display = f"\r⏱️{mins:02d}:{secs:02d}"
            sys.stdout.write(timer_display)
            sys.stdout.flush()
            time.sleep(1)
        print("\nTime’s up!")
        # Optional: play a system alert sound
        try:
            os.system("echo '\a'")  # works on most systems
        except:
            pass
    except KeyboardInterrupt:
        print("\nTimer stopped manually.")


def profiles_to_skip(profile_name):
    skip_list = [
        "Profile_01",
        # "Profile_02",
        # "Profile_03",
        # "Profile_04",
        # "Profile_05",
        # "Profile_06",
        # "Profile_07",
        # "Profile_08",
        # "Profile_09",
        # "Profile_10",
        # "Profile_11",
        # "Profile_12",
        # "Profile_13",
        # "Profile_14",
        # "Profile_15",
        # "Profile_16",
        # "Profile_17",
        # "Profile_18",
        # "Profile_19",
        # "Profile_20",
        # "Profile_21",
        # "Profile_22",
        # "Profile_23",
        # "Profile_24",
        # "Profile_25",
        # "Profile_26",
        # "Profile_27",
        # "Profile_28",
        # "Profile_29",
        # "Profile_30",
        # "Profile_31",
        # "Profile_32",
        # "Profile_33",
        # "Profile_34",
        # "Profile_35",
        # "Profile_36",
        # "Profile_37",
        # "Profile_38",
        # "Profile_39",
        # "Profile_40",
        # "Profile_41",
        # "Profile_42",
        # "Profile_43",
        # "Profile_44",
        # "Profile_45",
        # "Profile_46",
        # "Profile_47",
        # "Profile_48",
        # "Profile_49",
        # "Profile_50",
        # "Profile_51",
        # "Profile_52",
        # "Profile_53",
        # "Profile_54",
        # "Profile_55",
        # "Profile_56",
        # "Profile_57",
        # "Profile_58",
        # "Profile_59",
        # "Profile_60",
        # "Profile_61",
        # "Profile_62",
        # "Profile_63",
        # "Profile_64",
        # "Profile_65",
        # "Profile_66",
        # "Profile_67",
        # "Profile_68",
        # "Profile_69",
        # "Profile_70",
        # "Profile_71",
        # "Profile_72",
        # "Profile_73",
        # "Profile_74",
        # "Profile_75",
        # "Profile_76",
        # "Profile_77",
        # "Profile_78",
        # "Profile_79",
        # "Profile_80",
        # "Profile_81",
        # "Profile_82",
        # "Profile_83",
        # "Profile_84",
        # "Profile_85",
        # "Profile_86",
        # "Profile_87",
        # "Profile_88",
        # "Profile_89",
        # "Profile_90",
        # "Profile_91",
        # "Profile_92",
        # "Profile_93",
        # "Profile_94",
        # "Profile_95",
        # "Profile_96",
        # "Profile_97",
        # "Profile_98",
        # "Profile_99",
        # "Profile_100",
        # "Profile_101",
        # "Profile_102",
        # "Profile_103",
        # "Profile_104",
        # "Profile_105",
        # "Profile_106",
        # "Profile_107",
        # "Profile_108",
        # "Profile_109",
        # "Profile_110",
        # "Profile_111",
        # "Profile_112",
        # "Profile_113",
        # "Profile_114",
        # "Profile_115",
        # "Profile_116",
        # "Profile_117",
        # "Profile_118",
        # "Profile_119",
        # "Profile_120",
        # "Profile_121",
        # "Profile_122",
        # "Profile_123",
        # "Profile_124",
        # "Profile_125",
        # "Profile_126",
        # "Profile_127",
        # "Profile_128",
        # "Profile_129",
        # "Profile_130",
        # "Profile_131",
        # "Profile_132",
        # "Profile_133",
        # "Profile_134",
        # "Profile_135",
        # "Profile_136",
        # "Profile_137",
        # "Profile_138",
        # "Profile_139",
        # "Profile_140",
        # "Profile_141",
        # "Profile_142",
        # "Profile_143",
        # "Profile_144",
        # "Profile_145",
        # "Profile_146",
        # "Profile_147",
        # "Profile_148",
        # "Profile_149",
        # "Profile_150",
        # "Profile_151",
        # "Profile_152",
        # "Profile_153",
        # "Profile_154",
        # "Profile_155",
        # "Profile_156",
        # "Profile_157",
        # "Profile_158",
        # "Profile_159",
        # "Profile_160",
        # "Profile_161",
        # "Profile_162",
        # "Profile_163",
        # "Profile_164",
        # "Profile_165",
        # "Profile_166",
        # "Profile_167",
        # "Profile_168",
        # "Profile_169",
        # "Profile_170",
        # "Profile_171",
        # "Profile_172",
        # "Profile_173",
        # "Profile_174",
        # "Profile_175",
        # "Profile_176",
        # "Profile_177",
        # "Profile_178",
        # "Profile_179",
        # "Profile_180",
        # "Profile_181",
        # "Profile_182",
        # "Profile_183",
        # "Profile_184",
        # "Profile_185",
        # "Profile_186",
        # "Profile_187",
        # "Profile_188",
        # "Profile_189",
        # "Profile_190",
        # "Profile_191",
        # "Profile_192",
        # "Profile_193",
        # "Profile_194",
        # "Profile_195",
        # "Profile_196",
        # "Profile_197",
        # "Profile_198",
        # "Profile_199",
        # "Profile_200",
    ]
    return profile_name in skip_list


def update_order_count(json_path):
    if not os.path.exists(json_path):
        raise FileNotFoundError("JSON file not found.")

    # Read the file
    with open(json_path, "r") as f:
        data = json.load(f)

    # Validate required keys
    required_keys = ["total_order_to_place", "total_order_placed"]
    for key in required_keys:
        if key not in data:
            raise KeyError(f"Missing key in JSON: {key}")

    # Increment
    data["total_order_placed"] += 1

    # Write back
    with open(json_path, "w") as f:
        json.dump(data, f, indent=4)

    # Alert condition
    if data["total_order_placed"] >= data["total_order_to_place"]:
        print("ALERT: Order limit reached or exceeded!")
        return "limit_reached"

    return True  # optional


def get_profile_folders():
    url = f"{BASE_URL}/autonomous/agent/get_profile_folders"
    response = requests.get(url)
    return response.json()



new_accounts_folder          = os.getcwd() + "\\accounts"

# Ensure folders exist
Path(new_accounts_folder).mkdir(parents=True, exist_ok=True)


def load_storage(driver, account_credentials_data):
    data = account_credentials_data

    # Load cookies
    driver.get("https://www.jiomart.com")
    driver.delete_all_cookies()
    for cookie in data["cookies"]:
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass

    driver.refresh()

    for k, v in data["localStorage"].items():
        safe_k = json.dumps(k)
        safe_v = json.dumps(v)
        driver.execute_script(f"localStorage.setItem({safe_k}, {safe_v});")

    # Load SessionStorage
    for k, v in data["sessionStorage"].items():
        safe_k = json.dumps(k)
        safe_v = json.dumps(v)
        driver.execute_script(f"sessionStorage.setItem({safe_k}, {safe_v});")


    driver.refresh()
    print("[+] Session restored.")

def create_new_one_profile(new_accounts_folder):
    
    return new_accounts_folder + f"\\Profile_{str(int(time.time()))}"

def main():
    # Step 1: Get list of all Profile_ folders (full path)
    profile_folders = get_profile_folders()

    if not profile_folders:
        print("No Profile_ folders found.")
        return

    print(f"Found {len(profile_folders)} Profile_ folders.")
    
    # Step 2: Loop through each Profile_ folder
    for profile_path in profile_folders:
        profile_local_data = os.path.join(profile_path, "local_credentials.json")
        profile_name = profile_local_data.split(os.sep)[-2]
        
        if profiles_to_skip(profile_name):
            print(f"Skipping profile folder: {profile_name}")
            continue
        
        for i in range(1):
            print(profile_local_data)
            profile_headers_data = get_profile_info(profile_local_data)
            if not profile_headers_data:
                print(f"Could not retrieve headers for profile: {profile_name}")
                break
            if profile_headers_data:
                break

        if not profile_headers_data:
            print(f"Skipping profile due to missing headers: {profile_name}")
            continue
        
        
        if profile_headers_data:
            print(f"Processing: {profile_path.split(os.sep)[-1]}")
            
            
            try:
                result = automate(profile_headers_data, profile_path + "\\account_data.json", profile_name)
                if result == "order_limit_reached":
                    print("Order limit reached, stopping further processing.")
                    break
            except Exception as e:
                print(e)
                continue


if __name__ == "__main__":
    main()





