import requests
import time
import json
import os
import random



BASE_URL = "http://127.0.0.1:4080"
# BASE_URL = "https://nexonotp.in"

def configuration_data():
    configuration_file_path = r"c:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\configuration.json"
    url = f"{BASE_URL}/api/read/json_file"
    params = {"file_path": configuration_file_path}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return Exception(f"HTTP Error: {response.status_code}")
    elif response.json().get("success") != True:
        return Exception(f"API Error: {response.json().get('error')}")
    else:
        return response.json().get("data")

def store_data():
    configuration_file_path = r"c:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\stores.json"
    url = f"{BASE_URL}/api/read/json_file"
    params = {"file_path": configuration_file_path}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return Exception(f"HTTP Error: {response.status_code}")
    elif response.json().get("success") != True:
        return Exception(f"API Error: {response.json().get('error')}")
    else:
        return response.json().get("data")

def get_selected_accounts():
    configuration_file_path = r"C:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\selected_accounts.json"
    url = f"{BASE_URL}/api/read/json_file"
    params = {"file_path": configuration_file_path}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return Exception(f"HTTP Error: {response.status_code}")
    elif response.json().get("success") != True:
        return Exception(f"API Error: {response.json().get('error')}")
    else:
        return response.json().get("data")


def read_mock_names():
    configuration_file_path = r"C:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\customer_names.txt"
    url = f"{BASE_URL}/api/read/text_file"
    params = {"file_path": configuration_file_path}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return Exception(f"HTTP Error: {response.status_code}")
    elif response.json().get("success") != True:
        return Exception(f"API Error: {response.json().get('error')}")
    else:
        return response.json().get("content")




def get_profile_info(profile_local_credentials_name):
    # Check if the file exists
    if os.path.exists(profile_local_credentials_name):
        try:
            with open(profile_local_credentials_name, 'r', encoding='utf-8') as file:
                data = json.load(file)[0]
            return data
        except json.JSONDecodeError as e:
            print(f"Error: File exists but contains invalid JSON - {e}")
            return None
        except Exception as e:
            print(f"Unexpected error while reading the file: {e}")
            return None
    else:
        return False


def set_address(specific_headers, payload: dict):
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
        # Make the GET request
        resp1 = requests.post(url, headers=headers, json=payload)

        data = resp1.json()
        print(data)
        if data.get("status") == "success":
            address_id = data["result"]["address_id"]

            # Step 2: Set this address as preferred shipping address
            url_set_default = f"https://www.jiomart.com/mst/rest/v1/entity/customer/set_preferred_shipping_address/{address_id}"
            resp2 = requests.get(url_set_default, headers=headers, cookies=cookies)
            
            url_set_default = f"https://www.jiomart.com/mst/rest/v1/5/cart/save_address_v2_in_cart/shipping?address_id={address_id}"
            resp3 = requests.get(url_set_default, headers=headers, cookies=cookies)
            
            url_set_default = f"https://www.jiomart.com/mst/rest/v1/5/cart/save_address_v2_in_cart/billing?address_id={address_id}"
            resp4 = requests.get(url_set_default, headers=headers, cookies=cookies)
            
            url_set_default = f"https://www.jiomart.com/mst/rest/v1/address/v2/get/{address_id}"
            resp5 = requests.get(url_set_default, headers=headers, cookies=cookies)
            
        else:
            print("Failed to create address.")
        
    except Exception as e:
        return False




def random_name():
    
    names_list = read_mock_names().splitlines()
    """Return a random name from a given list."""
    if not names_list:
        return None  # in case the list is empty
    return random.choice(names_list)


def generate_random_floor():
    """Generate a random floor like '1st' to '6th'"""
    return random.choice(["1st", "2nd", "3rd", "4th", "5th", "6th"])

def random_phone():
    """Generate a random 10-digit phone number starting with 9/8/7"""
    return str(random.choice([9, 8, 7])) + "".join([str(random.randint(0,9)) for _ in range(9)])


STATUS_FILE = r"C:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\cloud_status.json"
recent_logs = []

def log_status(message, state="running", progress=None):
    global recent_logs
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    print(message) 
    recent_logs.insert(0, log_entry)
    if len(recent_logs) > 50:
        recent_logs = recent_logs[:50]
        
    data = {
        "state": state,
        "current_message": message,
        "progress": progress,
        "logs": recent_logs,
        "last_updated": time.time()
    }
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

while True:
    try:
        config_data = configuration_data()
        if isinstance(config_data, Exception):
            log_status(f"Error reading config: {config_data}", state="error")
            time.sleep(5)
            continue
            
        required_fields = {
            "mode": "all_once",
            "execution": "cloud",
            "pincode": None
        }
        
        current_exec = config_data.get("set_address", {}).get("execution")
        current_mode = config_data.get("set_address", {}).get("mode")
        
        if current_exec == required_fields.get("execution") and current_mode == required_fields.get("mode"):
            log_status("Starting Cloud Execution...", state="active")
            
            store_data_res = store_data()
            if isinstance(store_data_res, Exception):
                log_status(f"Error reading stores: {store_data_res}", state="error")
                time.sleep(5)
                continue
                
            # Find Pincode
            for store_pincode in store_data_res:
                if config_data.get("set_address").get("pincode") == store_pincode.get("pincode") and required_fields.get("pincode") is None:
                    log_status(f"Pincode found: {store_pincode.get('pincode')}", state="active")
                    required_fields["pincode"] = store_pincode.get("pincode")
                    break
            
            if required_fields.get("pincode") is None:
                log_status("No matching pincode found for cloud execution", state="waiting")
                time.sleep(3)
                continue
            
            selected_accs = get_selected_accounts()
            if isinstance(selected_accs, Exception) or not selected_accs:
                 log_status("No selected accounts found or error reading them", state="error")
                 time.sleep(5)
                 continue
                 
            log_status(f"Processing {len(selected_accs)} accounts", state="active", progress=f"0/{len(selected_accs)}")
            
            count = 0
            for account in selected_accs:
                count += 1
                profile_local_data = os.path.join(account, "local_credentials.json")
                profile_name = "Unknown"
                if os.sep in profile_local_data:
                    profile_name = profile_local_data.split(os.sep)[-2]
                
                log_status(f"Updating {profile_name}...", state="active", progress=f"{count}/{len(selected_accs)}")
                
                profile_headers_data = None
                for i in range(1): # Retry logic placeholder
                    profile_headers_data = get_profile_info(profile_local_data)
                    if profile_headers_data:
                        break
                
                if not profile_headers_data:
                    log_status(f"Skipping {profile_name} (Missing Headers)", state="active", progress=f"{count}/{len(selected_accs)}")
                    continue
                
                if isinstance(profile_headers_data, list):
                    profile_headers_data = profile_headers_data[0]
                
                # Find Lat/Lon
                lat_lon = ["0", "0"]
                for store_pincode in store_data_res:
                    if config_data.get("set_address").get("pincode") == store_pincode.get("pincode"):
                        lat_lon = store_pincode.get("latitude&longitude", "0, 0").split(", ")
                        break
                
                payload = {
                    "input_mode": "MAP_POLY",
                    "address_type": "home",
                    "addressee_name": random_name(),
                    "floor_no": generate_random_floor(),
                    "flat_or_house_no": config_data.get("set_address").get("owner_mark_prefix", ""),
                    "tower_no": None,
                    "building_type": "apartment",
                    "building_name": None,
                    "building_address": config_data.get("set_address").get("address", ""),
                    "area_name": config_data.get("set_address").get("landmark", ""),
                    "city": "Kolkata",
                    "state": "West Bengal",
                    "pin": config_data.get("set_address").get("pincode", ""),
                    "mobile_no": random_phone(),
                    "lat": lat_lon[0],
                    "lon": lat_lon[1],
                    "subs_eligible": False
                }
                
                try:
                    set_address(profile_headers_data, payload)
                    log_status(f"Success: Address set for {profile_name}", state="active", progress=f"{count}/{len(selected_accs)}")
                except Exception as e:
                    log_status(f"Failed {profile_name}: {e}", state="active", progress=f"{count}/{len(selected_accs)}")
            
            log_status("All accounts processed. Waiting for next command...", state="completed")
            
            try:
                cf_path = r"c:\Users\user\Desktop\jiomart_bugs\the_gtx_autonomous\configuration.json"
                if os.path.exists(cf_path):
                    with open(cf_path, "r") as f: chg_conf = json.load(f)
                    if chg_conf.get("set_address"):
                        chg_conf["set_address"]["execution"] = "completed"
                    with open(cf_path, "w") as f: json.dump(chg_conf, f, indent=4)
                    log_status("Cloud Batch execution finished. Mode set to 'completed'.", state="completed")
            except Exception as e:
                log_status(f"Error auto-updating config: {e}", state="error")
            time.sleep(5)
            
        else:
            log_status("Idle - Waiting for 'Cloud' execution mode...", state="idle")
            time.sleep(5)
            
    except Exception as e:
        print(f"Main Loop Error: {e}")
        time.sleep(5)