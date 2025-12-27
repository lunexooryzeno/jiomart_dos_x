import requests
import time
import json
import random
import os
from datetime import datetime
import argparse


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




# --- CONFIGURATION ---

# BASE_URL = "http://127.0.0.1:4080"
BASE_URL = "https://nexonotp.in"

CLOUD_STATUS_FILE = "cloud_status.json"

# --- GLOBAL STATE ---
orders_placed = 0
recent_logs = []
current_state = "idle"

def log_status(message):
    """Log to console and update the status file for the dashboard"""
    global orders_placed, recent_logs, current_state
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    print(entry)
    
    recent_logs.insert(0, entry)
    if len(recent_logs) > 50:
        recent_logs = recent_logs[:50]
    
    status_data = {
        "state": current_state,
        "current_message": message,
        "progress": f"{orders_placed} Orders Placed",
        "logs": recent_logs,
        "last_updated": datetime.now().timestamp()
    }
    
    try:
        with open(CLOUD_STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=4)
    except Exception as e:
        print(f"Error saving cloud status: {e}")

def get_remote_config():
    """Fetch configuration from the local control center API"""
    try:
        path = r"C:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\configuration.json"
        resp = requests.get(f"{BASE_URL}/api/read/json_file", params={"file_path": path})
        if resp.status_code == 200 and resp.json().get("success"):
            return resp.json().get("data")
    except:
        return None
    return None

def get_remote_accounts():
    """Fetch selected accounts from the local control center API"""
    try:
        path = r"C:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\selected_accounts.json"
        resp = requests.get(f"{BASE_URL}/api/read/json_file", params={"file_path": path})
        if resp.status_code == 200 and resp.json().get("success"):
            return resp.json().get("data")
    except:
        return []
    return []

def get_profile_info(path):
    """Fetch profile info from a specific json file via the control center"""
    try:
        resp = requests.get(f"{BASE_URL}/api/read/json_file", params={"file_path": path})
        if resp.status_code == 200 and resp.json().get("success"):
            return resp.json().get("data")
    except:
        return None
    return None

def get_accounts_data(path):
    """Fetch profile info from a specific json file via the control center"""
    try:
        resp = requests.get(f"{BASE_URL}/api/read/json_file", params={"file_path": path})
        if resp.status_code == 200 and resp.json().get("success"):
            return resp.json().get("data")
    except:
        return None
    return None

def get_remote_skip_list():
    """Fetch skip list from the local control center API"""
    try:
        path = r"C:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\skipped_accounts.json"
        resp = requests.get(f"{BASE_URL}/api/read/json_file", params={"file_path": path})
        if resp.status_code == 200 and resp.json().get("success"):
            return resp.json().get("data")
    except:
        return []
    return []

def add_to_remote_skip_list(profile_path):
    """Add a profile to the remote skip list via the control center"""
    skipped = get_remote_skip_list()
    if profile_path not in skipped:
        skipped.append(profile_path)
        try:
            requests.post(f"{BASE_URL}/api/gtx/skip-accounts/save", json={"skipped": skipped})
            log_status(f"🚫 Added {os.path.basename(profile_path)} to Remote Skip List.")
        except:
            pass

def stop_remote_execution():
    """Update global status to stopped in the main control center"""
    try:
        log_status("📡 Sending STOP command to Control Center...")
        resp = requests.post(f"{BASE_URL}/api/gtx/execution/update", json={"field": "status", "value": "stopped"})
        if resp.status_code == 200:
            log_status("✅ Control Center updated to STOPPED.")
        else:
            log_status(f"⚠️ Failed to stop Control Center. Status: {resp.status_code}")
    except Exception as e:
        log_status(f"❌ Error sending stop command: {e}")

def increment_remote_stats():
    """Increment order stats in the main control center"""
    try:
        requests.post(f"{BASE_URL}/api/gtx/order-stats/increment")
    except:
        pass

def record_successful_order(profile_path, cart_items):
    """Notify dashboard to record a successful order placement in shipment_tracking.json"""
    try:
        # Prepare order details for tracking following the full schema
        requests.post(f"{BASE_URL}/api/gtx/shipment/save", json={
            "profile_path": profile_path,
            "order_details": {}
        })
        log_status(f"📦 Order recorded in shipment tracking for {os.path.basename(profile_path)}")
    except Exception as e:
        log_status(f"⚠️ Failed to record shipment: {e}")

def send_notification(title, message):
    """Send a notification/request to the main dashboard notification tray"""
    try:
        requests.post(f"{BASE_URL}/api/gtx/permission/request", json={
            "account": title,
            "details": message
        })
    except:
        pass

def split_into_parts_function(folders, parts_count):
    """Split a list into N roughly equal groups"""
    total = len(folders)
    if parts_count <= 0: return [folders]
    base = total // parts_count
    extra = total % parts_count
    groups = []
    idx = 0
    for i in range(parts_count):
        size = base + (1 if i < extra else 0)
        groups.append(folders[idx: idx + size])
        idx += size
    return groups

# --- THROTTLING ENGINE ---

def apply_smart_throttling(limitations_config):
    """
    Calculate and execute wait time based on Throttling Rules:
    - no_limit: Full Velocity
    - per_min: Target Rate per minute
    - per_hour: Target Rate per hour
    - manual_confirmation: Wait for user to flip switch
    - fixed_delay: Standard sleep (Default)
    """
    global current_state
    
    throt = limitations_config.get("throttling", {})
    mode = throt.get("mode", "fixed_delay")
    val = float(throt.get("value", 5))

    wait_seconds = 0

    if mode == "no_limit":
        return # Zero delay
    
    if mode == "per_min":
        wait_seconds = 60.0 / val if val > 0 else 0
    elif mode == "per_hour":
        wait_seconds = 3600.0 / val if val > 0 else 0
    elif mode == "manual_confirmation":
        log_status("✋ MANUAL CONFIRMATION MODE: Pausing for user signal...")
        # In manual mode, we effectively 'pause' the engine via a status update
        # and wait for it to be set to 'running' again or for a manual trigger.
        # For simplicity in this demo, we'll wait for a specific 'permission' or 'resume'.
        # But per the requirement, we'll loop until status is 'running'.
        while True:
            conf = get_remote_config()
            if not conf: break
            if conf.get("execution_control", {}).get("status") == "running":
                break
            time.sleep(2)
        return
    else: # fixed_delay
        wait_seconds = val

    if wait_seconds > 0:
        log_status(f"Throttling: Waiting {wait_seconds:.1f}s (Rule: {mode})...")
        
        # Split sleep into 1s chunks to stay responsive to STOP/PAUSE
        end_time = time.time() + wait_seconds
        while time.time() < end_time:
            # Re-check global status
            latest = get_remote_config()
            if not latest or latest.get("execution_control", {}).get("status") != "running":
                log_status("Throttle interrupted: Status changed.")
                return
            
            # Sleep in small bits
            remaining = end_time - time.time()
            if remaining <= 0:
                break
            time.sleep(min(1, remaining))

# --- PERMISSION HANDLER ---

def check_manual_permission(profile_name, details="Order Placement"):
    """Request permission from the dashboard and wait for human approval"""
    global current_state
    
    config = get_remote_config()
    if not config: return True
    
    if not config.get("execution_control", {}).get("manual_permission", False):
        return True

    log_status(f"✋ Permission Required for {profile_name}. Requesting...")
    
    try:
        req_url = f"{BASE_URL}/api/gtx/permission/request"
        payload = {"account": profile_name, "details": details}
        resp = requests.post(req_url, json=payload)
        if resp.status_code != 200: return True
        req_id = resp.json().get("id")
        
        current_state = "waiting_approval"
        while True:
            latest = get_remote_config()
            if not latest or latest.get("execution_control", {}).get("status") != "running":
                current_state = "idle" if not latest else latest.get("execution_control", {}).get("status")
                return False
                
            status_url = f"{BASE_URL}/api/gtx/permission/status"
            status_resp = requests.get(status_url, params={"id": req_id})
            perm_status = status_resp.json().get("status")
            
            if perm_status == "approved":
                log_status(f"✓ Permission GRANTED for {profile_name}")
                current_state = "active"
                return True
            elif perm_status == "denied":
                log_status(f"✗ Permission DENIED for {profile_name}")
                current_state = "active"
                return False
            time.sleep(2)
    except Exception as e:
        log_status(f"Permission System Error: {e}")
        return True

# --- MOCK OPERATIONS ---

def mock_set_address(profile, addr_data):
    print(addr_data)
    log_status(f"Mock: Configuring Address for {profile} ({addr_data.get('pincode')})")
    time.sleep(1)
    return {"success": True, "message": "Address configured successfully"}

def mock_add_to_cart(profile, items):
    for item in items:
        p_name = item.get('product_name')
        p_code = item.get('product_code')
        p_qty = item.get('quantity')
        p_pin = item.get('pincode')
        log_status(f"Mock: Adding {p_name} to {profile} cart (Code: {p_code}, Qty: {p_qty}, Pin: {p_pin})")
    time.sleep(1)
    return {"success": True, "message": "Items added to cart"}

def mock_apply_coupon(profile, coupon):
    log_status(f"Mock: Applying coupon '{coupon}' for {profile}")
    time.sleep(0.5)
    return {"success": True, "message": f"Coupon {coupon} applied"}

def mock_place_order(profile):
    global orders_placed
    order_id = f"CLD-{random.randint(100000, 999999)}"
    log_status(f"Mock: SUCCESS! Order placed for {profile} -> ID: {order_id}")
    
    # Report to control center
    increment_remote_stats()
    orders_placed += 1
    
    return {"success": True, "order_id": order_id, "message": "Order placed successfully"}

def wait_while_paused():
    """Wait in a loop while the system is paused. Returns True if resumed, False if stopped."""
    global current_state
    log_status("⏸ System PAUSED. Standing by in current cycle...")
    current_state = "paused"
    while True:
        conf = get_remote_config()
        if not conf:
            time.sleep(5)
            continue
        
        status = conf.get("execution_control", {}).get("status", "stopped")
        if status == "running":
            log_status("▶ Resuming execution...")
            current_state = "active"
            return True
        if status == "stopped":
            return False
            
        time.sleep(2)



def load_storage(driver, account_data):
    # Load cookies
    driver.get("https://www.jiomart.com")
    driver.delete_all_cookies()
    for cookie in account_data["cookies"]:
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass

    driver.refresh()

    for k, v in account_data["localStorage"].items():
        safe_k = json.dumps(k)
        safe_v = json.dumps(v)
        driver.execute_script(f"localStorage.setItem({safe_k}, {safe_v});")

    # Load SessionStorage
    for k, v in account_data["sessionStorage"].items():
        safe_k = json.dumps(k)
        safe_v = json.dumps(v)
        driver.execute_script(f"sessionStorage.setItem({safe_k}, {safe_v});")


    driver.refresh()
    log_status("Session restored.")
store_code = "F1ZP"

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
    if coupon_code == "N0C0UP0N": return True
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



def delete_all_addresses(specific_headers):
    # Headers
    headers = {
        "authority": "www.jiomart.com",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        'authtoken': specific_headers.get("localStorage").get("authtoken"),
        "content-type": "application/json",
        "origin": "https://www.jiomart.com",
        "referer": "https://www.jiomart.com",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        'userid': specific_headers.get("localStorage").get("userid")
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
        all_addresses = requests.get(f"https://www.jiomart.com/mst/rest/v1/address/v2/get/all", headers=headers, cookies=cookies).json()

        # Extract all address IDs
        address_ids = [addr["id"] for addr in all_addresses["result"]["address_list"]]

        # Delete all addresses
        for address_id in address_ids:
            requests.get(f"https://www.jiomart.com/mst/rest/v1/address/v2/del/{address_id}", headers=headers, cookies=cookies)

    except Exception as e:
        raise e




def set_address_config(specific_headers, payload: dict):
    # Base URL
    url = "https://www.jiomart.com/mst/rest/v1/address/v2"
    
    # Headers
    headers = {
        "authority": "www.jiomart.com",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        'authtoken': specific_headers.get("localStorage").get("authtoken"),
        "content-type": "application/json",
        "origin": "https://www.jiomart.com",
        "referer": "https://www.jiomart.com",
        "sec-ch-ua": "\"Chromium\";v=\"136\", \"Google Chrome\";v=\"136\", \"Not.A/Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        'userid': specific_headers.get("localStorage").get("userid")
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
        # Make the POST request
        resp1 = requests.post(url, headers=headers, json=payload)
        data = resp1.json()
        
        if data.get("status") == "success":
            address_id = data["result"]["address_id"]
            # Set default address flows
            requests.get(f"https://www.jiomart.com/mst/rest/v1/entity/customer/set_preferred_shipping_address/{address_id}", headers=headers, cookies=cookies)
            requests.get(f"https://www.jiomart.com/mst/rest/v1/5/cart/save_address_v2_in_cart/shipping?address_id={address_id}", headers=headers, cookies=cookies)
            requests.get(f"https://www.jiomart.com/mst/rest/v1/5/cart/save_address_v2_in_cart/billing?address_id={address_id}", headers=headers, cookies=cookies)
            requests.get(f"https://www.jiomart.com/mst/rest/v1/address/v2/get/{address_id}", headers=headers, cookies=cookies)
            return data
        else:
            # {'status': 'fail', 'reason': {'reason_eng': 'cannot add anymore addresses. please consider dropping an address or updating an existing one.', 'reason_code': 'MAX_LIMIT_BREACH'}, 'response_time': '2025-12-22 23:55:08'}

            if data.get("status") == "fail" and data.get("reason").get("reason_code") == "MAX_LIMIT_BREACH":
                delete_all_addresses(specific_headers)
            
            return data
    except Exception as e:
        raise e



def store_data():
    configuration_file_path = r"c:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\stores.json"
    url = f"{BASE_URL}/api/read/json_file"
    try:
        params = {"file_path": configuration_file_path}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return Exception(f"HTTP Error: {response.status_code}")
        elif response.json().get("success") != True:
            return Exception(f"API Error: {response.json().get('error')}")
        else:
            return response.json().get("data")
    except Exception as e:
        return Exception(f"Connection Error: {e}")



def read_mock_names():
    configuration_file_path = r"C:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\customer_names.txt"
    url = f"{BASE_URL}/api/read/text_file"
    try:
        params = {"file_path": configuration_file_path}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return Exception(f"HTTP Error: {response.status_code}")
        elif response.json().get("success") != True:
            return Exception(f"API Error: {response.json().get('error')}")
        else:
            return response.json().get("content")
    except:
        return ""

def random_name():
    names_str = read_mock_names()
    if not names_str: return "JioMart Customer"
    names_list = names_str.splitlines()
    if not names_list: return "JioMart Customer"
    return random.choice(names_list)

def generate_random_floor():
    return random.choice(["1st", "2nd", "3rd", "4th", "5th", "6th"])

def random_phone():
    return str(random.choice([9, 8, 7])) + "".join([str(random.randint(0,9)) for _ in range(9)])



def verify_applied_coupon(coupon_code, specific_headers):
    if coupon_code == "N0C0UP0N": return True
    data = get_cart_data(specific_headers)
    if data.get("status") == "success":
        applied_coupon = data.get("result").get("cart").get("applied_coupons")
        if not applied_coupon or applied_coupon != coupon_code:
            return "coupon_not_applied"


## ---------------------------------------------------- ##


def automate(current_agent_idx, original_profile_path, specific_headers, account_data, use_proxy, cart_items, coupon_code, pincode, execution):
    def check_state():
        """Internal helper to check stop/pause/limit during mock"""
        latest = get_remote_config()
        if not latest: return "continue"
        
        status = latest.get("execution_control", {}).get("status")
        if status == "stopped": return "stopped"
        if status == "paused":
            if not wait_while_paused(): return "stopped"
            
        # Limit check
        limit = latest.get("limitations", {}).get("max_orders", -1)
        current = latest.get("order_stats", {}).get("placed_today", 0)
        if limit != -1 and current >= limit:
            return "limit_reached"
        
        return "continue"


    
    temp_profile_path = os.getcwd() + f"\\accounts\\Profile_{str(int(time.time()))}"
    profile_name = os.path.basename(original_profile_path)

    # (Optional) ignore certificate errors — useful if mitmproxy cert not imported
    options.add_argument("--ignore-certificate-errors")
    options.set_capability("acceptInsecureCerts", True)

    if execution in ["cloud", "both"]:
        options.add_argument(f"--user-data-dir={temp_profile_path}")
    else:
        options.add_argument(f"--user-data-dir={original_profile_path}")

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
        options.add_argument(f"--proxy-server=http://127.0.0.1:850{current_agent_idx}")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        return "chrome_start_error"


    if execution in ["cloud", "both"]:
        load_storage(driver, account_data)
        time.sleep(3)
    else:
        pass

    log_status(f"--- [MOCK MODE] Cycle for {profile_name} ---")



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
        log_status(f"Error in banner setup: {e}")
    
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
        if type(specific_headers) == list:
            specific_headers = specific_headers[0]
        
        data = get_cart_data(specific_headers)
        if not data:
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
        # Step 1: Init
        state = check_state()
        if state == "stopped": return "stopped"
        if state == "limit_reached":
            log_status(f"[MOCK] Stop: Max limit reached just before placement.")
            return "order_limit_reached"
        log_status(f"[MOCK] Initializing session...")
        time.sleep(1)
            
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
        
        
        # Init
        state = check_state()
        if state == "stopped": return "stopped"
        if state == "limit_reached":
            log_status(f"[MOCK] Stop: Max limit reached just before placement.")
            return "order_limit_reached"

        log_status(f"[MOCK] Clearing cart...")
        time.sleep(1)
        
        to_add = [i for i in cart_items if i.get("include_in_cart")]
        if not to_add:
            return "no_items_in_cart"
        

        # Set Items In Cart
        for item in to_add:
            product_name = item.get('product_name')
            product_id = item.get('product_code')
            product_qty = item.get('quantity')
            product_store_code = item.get('store_code')
            product_pin = item.get('pincode')

            log_status(f"Adding {product_name} to cart (Code: {product_id}, Qty: {product_qty}, Store: {product_store_code})")
            response = add_item_with_retry(product_id, product_qty, specific_headers, product_pin, product_store_code, product_name)
            if not response:
                log_status(f"Failed to add {product_name} to cart.")
                send_notification("CRITICAL ERROR", f"Failed to add {product_name} to cart. Stopping execution.")
                stop_remote_execution()
                return "failed_to_add_item_to_cart"
        
        # Now try to apply coupon
        # Init
        state = check_state()
        if state == "stopped": return "stopped"
        if state == "limit_reached":
            log_status(f"[MOCK] Stop: Max limit reached just before placement.")
            return "order_limit_reached"
        data = get_cart_data(specific_headers)
        if not data:
            print("Failed to retrieve cart data, possibly due to invalid headers or profile logged out.")
            driver.quit()
            return "failed_due_to_invalid_headers"
        
        if data.get("status") == "success":
            applied_coupon = data.get("result").get("cart").get("applied_coupons")
            if not applied_coupon:
                if apply_coupon(coupon_code, specific_headers):
                    print(f"Coupon successfully applied! '{coupon_code}' directly.")
                else:
                    print(f"Failed to apply coupon after all attempts! '{coupon_code}'.{profile_name}")
                    driver.quit()
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
                        driver.quit()
                        return "failed_to_apply_coupon"
                else:
                    print(f"Failed to unapply existing coupon: {applied_coupon[0]}. {profile_name}")
                    driver.quit()
                    return "failed_to_unapply_existing_coupon"
        else:
            print("Failed to retrieve cart data.")
            driver.quit()
            return "failed_to_retrieve_cart_data"
            
        

        response = verify_applied_coupon(coupon_code, specific_headers)
        if response == "coupon_not_applied":
            driver.quit()
            return "coupon_not_applied"


        try:
            # Click on "Delivery to"
            log_status("Clicking on 'Delivery to'...")
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.deliver-to"))).click()
            time.sleep(2)
            
            # Click on the address item
            log_status("Selecting address item...")
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.addressitem"))).click()
            time.sleep(2)
        except Exception as e:
            log_status(f"Error during address selection: {e}")


        driver.refresh()
        
        # Init
        state = check_state()
        if state == "stopped": return "stopped"
        if state == "limit_reached":
            log_status(f"[MOCK] Stop: Max limit reached just before placement.")
            return "order_limit_reached"
        

        
        
        
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
        
        
        
        log_status("Clicked on place order")
        # Init
        state = check_state()
        if state == "stopped": return "stopped"
        if state == "limit_reached":
            log_status(f"[MOCK] Stop: Max limit reached just before placement.")
            return "order_limit_reached"
        try:
            # Wait for page to be fully loaded
            WebDriverWait(driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except:
            return "timeout"
            
        

        try:
            # Wait for the Make Payment button to be clickable and click it
            make_payment_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='button Make Payment']")))
            make_payment_button.click()
        except:
            try:
                log_status("Make Payment button not found, trying 'Deliver Here' button...")
                # Try to click on Deliver Here button if Make Payment fails
                deliver_here_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='button Deliver Here']")))
                deliver_here_button.click()
                time.sleep(2)
                log_status("Retrying 'Make Payment' button...")
                # Try Make Payment again after clicking Deliver Here
                make_payment_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='button Make Payment']")))
                make_payment_button.click()
            except:
                log_status("Failed to click on 'Deliver Here' or retry 'Make Payment'")
                return "failed_to_click_make_payment"
        
        log_status("Clicked on make payment")
        # Init
        state = check_state()
        if state == "stopped": return "stopped"
        if state == "limit_reached":
            log_status(f"[MOCK] Stop: Max limit reached just before placement.")
            return "order_limit_reached"
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
        # Init
        state = check_state()
        if state == "stopped": return "stopped"
        if state == "limit_reached":
            log_status(f"[MOCK] Stop: Max limit reached just before placement.")
            return "order_limit_reached"
        
        
        # Step 1: Scroll to bottom to make sure COD section is visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)  # wait for any lazy loading
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
            driver.quit()
                
            return "order_placed_success"
        except Exception as e:
            print(f"Failed to click Proceed button: {str(e)}")
            raise

    except Exception as e:
        driver.quit()
        print(f"An error occurred in automation: {str(e)}")
        traceback.print_exc()
        return "automation_error"



def automate_mock(current_agent_idx, original_profile_path, specific_headers, account_data, use_proxy, cart_items, coupon):
    profile_name = os.path.basename(original_profile_path)
    log_status(f"--- [MOCK MODE] Cycle for {profile_name} ---")
    
    def check_state():
        """Internal helper to check stop/pause/limit during mock"""
        latest = get_remote_config()
        if not latest: return "continue"
        
        status = latest.get("execution_control", {}).get("status")
        if status == "stopped": return "stopped"
        if status == "paused":
            if not wait_while_paused(): return "stopped"
            
        # Limit check
        limit = latest.get("limitations", {}).get("max_orders", -1)
        current = latest.get("order_stats", {}).get("placed_today", 0)
        if limit != -1 and current >= limit:
            return "limit_reached"
        
        return "continue"

    # Step 1: Init
    state = check_state()
    if state == "stopped": return "stopped"
    if state == "limit_reached":
        log_status(f"[MOCK] Stop: Max limit reached just before placement.")
        return "order_limit_reached"
    log_status(f"[MOCK] Initializing session...")
    time.sleep(1)
    
    # Step 2: Cart
    state = check_state()
    if state == "stopped": return "stopped"
    if state == "limit_reached":
        log_status(f"[MOCK] Stop: Max limit reached just before placement.")
        return "order_limit_reached"
    log_status(f"[MOCK] Clearing cart...")
    time.sleep(1)
    
    to_add = [i for i in cart_items if i.get("include_in_cart")]
    if not to_add:
        return "no_items_error"
    print(to_add)
    mock_add_to_cart(profile_name, to_add)
    
    # Step 3: Coupon
    state = check_state()
    if state == "stopped": return "stopped"
    if state == "limit_reached":
        log_status(f"[MOCK] Stop: Max limit reached just before placement.")
        return "order_limit_reached"
    if coupon:
        mock_apply_coupon(profile_name, coupon)
    
    # Step 4: Final Placement
    state = check_state()
    if state == "stopped": return "stopped"
    if state == "limit_reached":
        log_status(f"[MOCK] Stop: Max limit reached just before placement.")
        return "order_limit_reached"
        
    log_status(f"[MOCK] Finalizing checkout for {profile_name}...")
    time.sleep(1.5)
    
    res = mock_place_order(profile_name)
    if res.get("success"):
        return "order_placed_success"
    else:
        return "failed_to_place_order"
    

# --- MAIN EXECUTION ENGINE ---

def start_agent(current_agent_idx: int, executions: list):
    global current_state, orders_placed
    log_status("GTX Cloud Agent Starting...")
    
    # Reset tracker for a clean start of the agent session
    orders_placed = 0 
    limit_notified = False
    
    while True:
        
        config = get_remote_config()
        if not config:
            log_status("Connection Lost: Waiting for Local Control Center...")
            time.sleep(5)
            continue

        # Sync local counter with remote source of truth (placed_today)
        orders_placed = config.get("order_stats", {}).get("placed_today", 0)

        exec_ctrl = config.get("execution_control", {})
        status = exec_ctrl.get("status", "stopped")
        target = exec_ctrl.get("target_scope", "both")

        # 0. Global Limit Check (Dashboard Level)
        limitations = config.get("limitations", {})
        max_total = limitations.get("max_orders", -1)
        if max_total != -1 and orders_placed >= max_total:
            if not limit_notified:
                log_status(f"🛑 LIMIT REACHED: {orders_placed}/{max_total}. Notifying Dashboard and stopping engine...")
                send_notification("LIMIT REACHED", f"Order limit ({max_total}) has been reached. System is standing by.")
                stop_remote_execution()
                limit_notified = True
            current_state = "idle"
            time.sleep(10)
            continue
        else:
            limit_notified = False

        if status == "stopped":
            current_state = "idle"
            log_status("System is STOPPED. Waiting for Start signal...")
            time.sleep(5)
            continue

        if status == "paused":
            # If we start in paused state, wait at the gate
            if not wait_while_paused(): continue
            # Re-fetch config after resume
            config = get_remote_config()

        if target not in executions:
            current_state = "idle"
            log_status(f"Scope is '{target}'. Local processing omitted.")
            time.sleep(5)
            continue

        current_state = "active"
        accounts = get_remote_accounts()
        if not accounts:
            log_status("Resource Error: No accounts selected for execution.")
            time.sleep(10)
            continue

        limitations = config.get("limitations", {})
        max_total = limitations.get("max_orders", -1)
        per_account = limitations.get("orders_per_account", 1)
        use_proxy = limitations.get("use_proxy", False)
        
        addr_config = config.get("set_address", {})
        is_dynamic_address = addr_config.get("mode") == "each_time"

        cart = config.get("cart_items", {})
        cart_items = cart.get("items", [])
        coupon = cart.get("coupon")

        # Split Execution Logic
        split_cfg = limitations.get("split_execution", {})
        split_enabled = split_cfg.get("enabled", False)
        
        # Agent 1: Skip split logic if split execution is not enabled
        if current_agent_idx == 1:
            if not split_enabled:
                log_status(f"Agent {current_agent_idx}: Split execution is disabled. Processing all accounts.")
            else:
                # Split is enabled for Agent 1
                parts_count = split_cfg.get("parts", 1)
                groups = split_into_parts_function(accounts, parts_count)
                if 0 < current_agent_idx <= len(groups):
                    accounts = groups[current_agent_idx - 1]
                    log_status(f"✂️ Split Mode: Agent {current_agent_idx} handling Part {current_agent_idx}/{parts_count} ({len(accounts)} accounts)")
        
        # Other Agents (2, 3, 4, etc.): Must wait for split execution to be enabled
        else:
            while not split_enabled:
                log_status(f"⏸️ Agent {current_agent_idx}: Waiting for split execution to be enabled... (refreshing every 7 seconds)")
                time.sleep(7)
                
                # Refresh config to check if split is enabled
                config = get_remote_config()
                if not config:
                    log_status("Connection Lost: Waiting for Local Control Center...")
                    time.sleep(5)
                    continue
                
                split_cfg = config.get("limitations", {}).get("split_execution", {})
                split_enabled = split_cfg.get("enabled", False)
                limitations = config.get("limitations", {})
            
            # Split is now enabled, check if this agent's part is valid
            parts_count = split_cfg.get("parts", 1)
            
            if current_agent_idx <= parts_count:
                groups = split_into_parts_function(accounts, parts_count)
                if 0 < current_agent_idx <= len(groups):
                    accounts = groups[current_agent_idx - 1]
                    log_status(f"✂️ Split Mode: Agent {current_agent_idx} handling Part {current_agent_idx}/{parts_count} ({len(accounts)} accounts)")
                else:
                    log_status(f"❌ Agent {current_agent_idx}: Part index out of range. No accounts to process.")
                    time.sleep(10)
                    continue
            else:
                log_status(f"⏭️ Agent {current_agent_idx}: Current part ({current_agent_idx}) exceeds total parts ({parts_count}). Skipping execution.")
                time.sleep(10)
                continue

        # Check if non-Agent-1 has 0 accounts - wait for accounts to become available
        if current_agent_idx != 1 and len(accounts) == 0:
            while len(accounts) == 0:
                log_status(f"⏸️ Agent {current_agent_idx}: No accounts assigned. Waiting for accounts... (refreshing every 7 seconds)")
                time.sleep(7)
                
                # Refresh config and re-check split configuration
                config = get_remote_config()
                if not config:
                    log_status("Connection Lost: Waiting for Local Control Center...")
                    time.sleep(5)
                    continue
                
                # Re-fetch accounts
                accounts = get_remote_accounts()
                if not accounts:
                    log_status(f"Agent {current_agent_idx}: Still no accounts available in system.")
                    continue
                
                # Re-apply split logic
                limitations = config.get("limitations", {})
                split_cfg = limitations.get("split_execution", {})
                split_enabled = split_cfg.get("enabled", False)
                
                if split_enabled:
                    parts_count = split_cfg.get("parts", 1)
                    if current_agent_idx <= parts_count:
                        groups = split_into_parts_function(accounts, parts_count)
                        if 0 < current_agent_idx <= len(groups):
                            accounts = groups[current_agent_idx - 1]
                            if len(accounts) > 0:
                                log_status(f"✅ Agent {current_agent_idx}: Now assigned {len(accounts)} accounts from Part {current_agent_idx}/{parts_count}")
                                break
                        else:
                            accounts = []
                    else:
                        log_status(f"Agent {current_agent_idx}: Part index ({current_agent_idx}) still exceeds total parts ({parts_count})")
                        accounts = []
                else:
                    log_status(f"Agent {current_agent_idx}: Split execution is still disabled.")
                    accounts = []
        
        log_status(f"Ready. Processing {len(accounts)} accounts.")
        skip_list = get_remote_skip_list()

        for profile_path in accounts:
            if profile_path in skip_list:
                log_status(f"⏩ Skipping {os.path.basename(profile_path)} (In Skip List)")
                continue

            profile_name = os.path.basename(profile_path)
            profile_local_data = os.path.join(profile_path, "local_credentials.json")
            profile_name = profile_local_data.split(os.sep)[-2]


            dynamic_addresses_set = False
            
            # Account-level control loop
            for i in range(per_account):
                # 1. STOP/PAUSE Check (Before doing anything)
                latest_conf = get_remote_config()
                if not latest_conf: 
                    time.sleep(5)
                    continue
                
                status = latest_conf.get("execution_control", {}).get("status")
                
                if status == "paused":
                    if not wait_while_paused():
                        log_status("🛑 STOPPED while paused. Resetting agent.")
                        return # Exit start_agent to restart from beginning
                elif status == "stopped":
                    log_status("🛑 STOPPED. Resetting agent.")
                    return # Exit start_agent to restart from beginning

                # 2. Total Limit Check (Fast exit from cycle)
                if max_total != -1 and orders_placed >= max_total:
                    break # Return to outer loop to handle notification/waiting

                # 3. MANUAL PERMISSION CHECK (Before every single order)
                if not check_manual_permission(profile_name, f"Order {i+1}/{per_account} for {profile_name}"):
                    log_status(f"Execution Denied for {profile_name} skip cycle.")
                    continue

                log_status(f"--- Cycle {i+1}/{per_account} for {profile_name} ---")
                
                headers_data = get_profile_info(os.path.join(profile_path, "local_credentials.json"))
                if not headers_data:
                    log_status(f"Could not retrieve headers for {profile_name}. Skipping profile and adding to Skip List.")
                    add_to_remote_skip_list(profile_path)
                    break # Break inner loop to move to next profile

                if type(headers_data) == list:
                    headers_data = headers_data[0]

                accounts_data = get_accounts_data(os.path.join(profile_path, "account_data.json"))
                if not accounts_data:
                    log_status(f"Could not retrieve accounts data for {profile_name}. Skipping profile and adding to Skip List.")
                    add_to_remote_skip_list(profile_path)
                    break # Break inner loop to move to next profile

                if type(accounts_data) == list:
                    accounts_data = accounts_data[0]
                
                if is_dynamic_address and not dynamic_addresses_set:
                    store_data_res = store_data()
                    if isinstance(store_data_res, Exception):
                        log_status(f"Error reading stores: {store_data_res}", state="error")
                        time.sleep(5)
                        continue
                        
                    # Find Pincode in store data
                    found_pincode = None
                    target_pincode = latest_conf.get("set_address", {}).get("pincode")
                    for store_pincode in store_data_res:
                        if target_pincode == store_pincode.get("pincode"):
                            log_status(f"Pincode found: {store_pincode.get('pincode')}")
                            found_pincode = store_pincode.get("pincode")
                            break
                    
                    if found_pincode is None:
                        log_status(f"❌ CRITICAL: No matching pincode found for {target_pincode} in stores.json. Stopping Engine.")
                        send_notification("PINCODE ERROR", f"The pincode {target_pincode} was not found in stores.json. Execution halted.")
                        stop_remote_execution()
                        break
                    
                    # Find Lat/Lon
                    lat_lon = ["0", "0"]
                    for store_pincode in store_data_res:
                        if config.get("set_address").get("pincode") == store_pincode.get("pincode"):
                            lat_lon = store_pincode.get("latitude&longitude", "0, 0").split(", ")
                            break
                    
                    payload = {
                        "input_mode": "MAP_POLY",
                        "address_type": "home",
                        "addressee_name": random_name(),
                        "floor_no": generate_random_floor(),
                        "flat_or_house_no": config.get("set_address").get("owner_mark_prefix", ""),
                        "tower_no": None,
                        "building_type": "apartment",
                        "building_name": None,
                        "building_address": config.get("set_address").get("address", ""),
                        "area_name": config.get("set_address").get("landmark", ""),
                        "city": "Kolkata",
                        "state": "West Bengal",
                        "pin": config.get("set_address").get("pincode", ""),
                        "mobile_no": random_phone(),
                        "lat": lat_lon[0],
                        "lon": lat_lon[1],
                        "subs_eligible": False
                    }

                    

                    
                    set_address_response = set_address_config(headers_data, payload)
                    if set_address_response.get("status") == "fail":
                        set_address_response = set_address_config(headers_data, payload)
                        if set_address_response.get("status") == "success":
                            dynamic_addresses_set = True
                        else:
                            log_status(f"Failed to set dynamic address for {profile_name}. Skipping cycle.")
                            log_status(f"The error message is: {set_address_response.get('reason').get('reason_eng')}")
                            continue        
                    if set_address_response.get("status") == "success":
                        dynamic_addresses_set = True
                    else:
                        log_status(f"Failed to set dynamic address for {profile_name}. Skipping cycle.")
                        log_status(f"The error message is: {set_address_response.get('reason').get('reason_eng')}")
                        continue
                
                automate_response = automate(current_agent_idx, profile_path, headers_data, accounts_data, use_proxy, cart_items, coupon, latest_conf.get("set_address", {}).get("pincode"), target)
                # automate_response = automate_mock(current_agent_idx, profile_path, headers_data, accounts_data, use_proxy, cart_items, coupon)
                if automate_response == "chrome_start_error":
                    log_status("Chrome failed to start. Skipping cycle.")
                    add_to_remote_skip_list(profile_path)
                    break 
                elif automate_response == "failed_due_to_invalid_headers":
                    log_status("Failed to retrieve cart data, possibly due to invalid headers or profile logged out. Skipping cycle.")
                    add_to_remote_skip_list(profile_path)
                    break 
                elif automate_response == "failed_to_retrieve_cart_data":
                    log_status("Failed to retrieve cart data, possibly due to invalid headers or profile logged out. Skipping cycle.")
                    add_to_remote_skip_list(profile_path)
                    break 
                elif automate_response == "failed_to_clear_cart":
                    log_status("Failed to clear cart, possibly due to invalid headers or profile logged out. Skipping cycle.")
                    add_to_remote_skip_list(profile_path)
                    break 
                elif automate_response == "profile_logout":
                    log_status(f"Profile {profile_name} is LOGGED OUT. Adding to Skip List.")
                    add_to_remote_skip_list(profile_path)
                    break 
                elif automate_response == "order_limit_exceeds":
                    log_status(f"Profile {profile_name} order limit exeeds. Adding to Skip List.")
                    add_to_remote_skip_list(profile_path)
                    break 
                elif automate_response == "timeout":
                    log_status(f"Profile {profile_name} timeout.")
                    continue
                if automate_response == "order_placed_success":
                    log_status(f"✅ Success! Order placed for {profile_name}.")
                    record_successful_order(profile_path, cart_items)
                    orders_placed += 1

                # 4. ADVANCED THROTTLING
                # Skip automated throttling if Manual Permission is active (Human delay is sufficient)
                if not latest_conf.get("execution_control", {}).get("manual_permission", False):
                    apply_smart_throttling(limitations)
                else:
                    log_status("Throttling skipped: Manual Permission is ACTIVE.")

        # Check if this agent actually processed accounts or just had 0 assigned
        # Non-Agent-1 with 0 accounts should loop back, not stop
        if current_agent_idx != 1 and len(accounts) == 0:
            log_status(f"Agent {current_agent_idx}: No accounts were assigned in this cycle. Looping back to check for updates...")
            time.sleep(5)
            continue
        
        log_status("🏁 All available accounts processed. Resources Exhausted.")
        send_notification("RESOURCES EXHAUSTED", f"Processed all available accounts. Placed {orders_placed} total orders.")
        stop_remote_execution()
        current_state = "idle"
        time.sleep(5)

if __name__ == "__main__":
    try:
        # Setup argument parser
        parser = argparse.ArgumentParser(description='Local Autonomous Agent')
        parser.add_argument('--idx', type=int, default=1, help='Agent index (default: 1)')
        args = parser.parse_args()
        
        current_agent_idx = args.idx
        environment = "cloud"
        executions = [environment, "both"]
        start_agent(current_agent_idx, executions)
    except KeyboardInterrupt:
        current_state = "stopped"
        log_status("Cloud Agent Shutdown.")
