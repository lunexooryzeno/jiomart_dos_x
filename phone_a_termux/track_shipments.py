import os
import json
import time
import traceback
import requests
from requests_toolbelt import MultipartEncoder
import re
from datetime import datetime
import hashlib

# Profile Path Location Full Location Based


import time
# ------------------------------------------------------ #
# Universal Variables
# ------------------------------------------------------ #
# BASE_URL = "http://127.0.0.1:4080"
BASE_URL = "https://nexonotp.in"


what_is_the_jiomart_order_limit = input("Enter the Jiomart order limit for alerts (e.g., 5): ")
try:
    what_is_the_jiomart_order_limit = int(what_is_the_jiomart_order_limit)
except ValueError:
    print("Invalid input. Please enter a numeric value.")
    exit(1)


# ------------------------------------------------------ #








# Original topic name
accepted_topic = "P9Xj3RkM2tY7uWqL8sG0vBzNdCfEh"

# Get today's date in DD-MM-YYYY format
today_str = datetime.now().strftime("%d-%m-%Y")

# Concatenate topic with date
topic_with_date = f"{accepted_topic}{today_str}"

# Generate MD5 hash
md5_hash = hashlib.md5(topic_with_date.encode()).hexdigest()

# Final topic strings
ntfy_accepted_topic = "ac" + md5_hash
ntfy_shipped_topic = "sh" + md5_hash
ntfy_final_status_topic = "st" + md5_hash

def get_pending_list():
    url = f"{BASE_URL}/shipments/pending/list"
    response = requests.get(url)
    return response.json()["data"]


grab_tracking_header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "connection": "keep-alive",
    "host": "track.grab.in",
    "referer": "https://www.jiomart.com/",
    "sec-ch-ua": "\"Not.A/Brand\";v=\"99\", \"Chromium\";v=\"136\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "iframe",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-storage-access": "none",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
}

def extract_rider_data(html_content):
    """Extract rider data from HTML content."""
    selfie_match = re.search(r'src="(https://prodakscdn\.grab\.in/grabprod-authservice/rider_checkin_selfie/[^"]+)"', html_content)
    selfie_url = selfie_match.group(1) if selfie_match else None

    tel_match = re.search(r'href="tel:(\d+)"', html_content)
    telephone = tel_match.group(1) if tel_match else None

    name_match = re.search(r'<p class="mb-0 w-100 _2341"[^>]*>([^<]+)</p>', html_content)
    name = name_match.group(1).strip() if name_match else None

    rider_id = None
    if selfie_url:
        id_match = re.search(r'/LIVE/([A-Z0-9]+)/', selfie_url)
        rider_id = id_match.group(1) if id_match else None

    return {
        "rider_checkin_selfie": selfie_url,
        "rider_telephone": telephone,
        "rider_name": name,
        "rider_id": rider_id
    }


def send_notification_for_delivery(data, ntfy_shipped_topic):
    """Send extracted rider + customer data to ntfy."""
    # Group and count by product name
    item_summary = {}
    for item in data.get("items", []):
        name = item["product_name"]
        item_summary[name] = item_summary.get(name, 0) + 1

    # Sort by quantity (lowest → highest)
    sorted_summary = sorted(item_summary.items(), key=lambda x: x[1])

    # Create string summary
    item_summary_str = ",\n\n    ".join(f"{qty} × {name}" for name, qty in sorted_summary)
    
    print(data.get("order_id"))

        
    message = f"""
** **\n
**Profile Identity&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :** `{data.get("profile_name")}`  
**Customer Name&nbsp;&nbsp;&nbsp; :** `{data.get("firstname")}` 

**Order Number&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :** `{data.get("order_id")[:-4]}` **{data.get("order_id")[14:]}**  
**Invoice Amount&nbsp;&nbsp;&nbsp;&nbsp; :** `₹{data.get("order_amount")}` 

**Payment Mode&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :** `{data.get("cod_allowed")}` 

**Order Date&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :** `{data.get("order_date")}` 

**Delivery Code&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :** **{data.get("delivery_code")}** 

**Total Items&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; :** `{data.get("total_item")}` 

---

<details>

    {item_summary_str}
    
</details>

---

**Rider Identity&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:** `{data['rider_id']}`  
**Rider Name&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:** `{data['rider_name']}`

**Rider Phone&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:** [{data['rider_telephone'][:3]}&nbsp;{data['rider_telephone'][3:6]}&nbsp;{data['rider_telephone'][6:]}](tel:{data['rider_telephone']})

**Accepted Data&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:** [Click Here]({ntfy_shipped_topic + rider_data["rider_id"]})

---
"""
    response = requests.post("https://ntfy.sh/",
        data=json.dumps({
            "topic": ntfy_shipped_topic,
            "message": message,
            "title": "📦 Order Accepted by Rider",
            "priority": 4,
            "attach": f"{data['rider_checkin_selfie']}",
            "actions": [{ "action": "view", "label": "Call Now", "url": f"tel:{data['rider_telephone']}", "label": "Send Otp", "url": f"https://wa.me/91{data['rider_telephone']}?text=%2A%20Rider%20Identity%20%3A%E2%80%82{data['rider_id']}%0A%2A%20Rider%20Name%20%3A%E2%80%82{data['rider_name']}%0A%2A%20Customer%20Name%20%3A%E2%80%82{data.get("firstname")}%0A%2A%20Shipment%20Identity%20%3A%E2%80%82{data.get("order_id")[:-4]}%20%2A{data.get("order_id")[14:]}%2A%0A%2A%20Invoice%20Amount%20%3A%E2%80%82%E2%82%B9{data.get("order_amount")}%0A%2A%20Payment%20Mode%20%3A%E2%80%82{data.get("cod_allowed")}%E2%80%82%0A%2A%20Delivery%20Code%20%3A%20%2A{data.get("delivery_code")}%2A" }]
        }),
        headers={ "Markdown": "yes" }
    )
    
    return response.status_code == 200




def read_json(full_path):
    url = f"{BASE_URL}/shipments/pending/read"
    payload = {"path": full_path}
    response = requests.post(url, json=payload)
    return response.json()


def get_profile_info(profile_local_credentials_name):
    try:
        return read_json(profile_local_credentials_name)["data"]
    except Exception as e:
        return None





def get_recent_jiomart_order(specific_headers, profile_local_data):
    # API endpoint
    url = "https://www.jiomart.com/hcat/rest/v1/myorders/getmainorders"
    
    # Headers from the request
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'en-US,en;q=0.9',
        'authtoken': specific_headers.get("localStorage").get("authtoken"),
        'origin': 'https://www.jiomart.com',
        'referer': 'https://www.jiomart.com/customer/orderhistory',
        'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
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
    
    # Form data with the required parameters
    form_data = {
        'pageIndex': '1',
        'pageSize': '10',
        'userid': specific_headers.get("localStorage").get("userid")
    }
    
    try:
        # Make the POST request
        response = requests.post(url, headers=headers, cookies=cookies, data=form_data)
        
        # Check if request was successful
        if response.status_code == 200:
            
            # Try to parse JSON response
            try:
                json_response = response.json()
                
                # Check if the response has the expected structure
                if json_response.get('status') == 'success' and 'result' in json_response:
                    result = json_response['result']
                    
                    # Get total order count
                    total_orders = result.get('totalOrderCnt', 0)
                    
                    # Get order list
                    order_list = result.get('orderList', [])
                    
                    overall_data = []
                    
                    # print(order_list)
                    
                    if order_list:
                        
                        # Get today's date in same format as JSON uses (e.g., "9 October 2025")
                        today_str = datetime.now().strftime("%#d %B %Y")  # Use %#d on Windows

                        # Counters
                        cancelled_count = 0
                        delivered_count = 0
                        returned_count = 0  # In case you add returned orders later

                        # Check all orders
                        for order in order_list:
                            try:
                                status = order.get("display_status").get("header_status").split("\n")[-1].lower()
                            except: continue
                            delivered_date = order.get("delivered_date", "")

                            # Count based on same-day condition
                            if re.search(r"cancel", status) and today_str in order.get("purchased_date", ""):
                                cancelled_count += 1
                            if re.search(r"deliver", status) and delivered_date == today_str:
                                delivered_count += 1
                            if re.search(r"return", status) and delivered_date == today_str:
                                returned_count += 1

                        # Total same-day actions
                        total_today = cancelled_count + delivered_count + returned_count

                        # If more than or equal to 5, alert
                        if total_today >= what_is_the_jiomart_order_limit:
                            print(f"ALERT: {total_today} orders (Cancelled/Delivered/Returned) happened today!")
                            print("Let me just remove this profile from orders_profile.json...")
                            try:
                                remove_profile_from_orders(profile_local_data)
                            except Exception as e:
                                print(e)
                                traceback.print_exc()
                        else:
                            print(f"No alert — only {total_today} orders affected today.")
                        

                        for orders in order_list:
                            try:
                                order_status = orders.get("display_status").get("header_status").split("\n")[-1].lower()
                            except:
                                order_status = 'cancel'
                                pass
                            
                            if re.search(r"delivered", order_status): pass
                            elif re.search(r"cancel", order_status): continue
                            elif re.search(r"ordered", order_status):
                                # Get the most recent order (first in the list)
                                recent_order = orders
                                
                                # Extract all the details
                                order_details = {
                                    'order_id': recent_order.get('order_id', 'N/A'),
                                    'shipment_id': recent_order.get('shipment_id', 'N/A'),
                                    'status': recent_order.get('display_status', {}).get('header_status', 'N/A'),
                                    'amount': recent_order.get('order_amount', 'N/A'),
                                    'date': recent_order.get('purchased_date', 'N/A'),
                                    'item_count': len(recent_order.get('item_details', [])),
                                    'items': []
                                }
                                
                                # Get all items
                                items = recent_order.get('item_details', [])
                                for item in items:
                                    order_details['items'].append({
                                        'product_name': item.get('product_name', 'N/A'),
                                        'sku_code': item.get('skucode', 'N/A'),
                                        'product_image': item.get('product_image', 'N/A')
                                    })
                                
                                overall_data.append(order_details)
                            elif re.search(r"under", order_status):
                                # Get the most recent order (first in the list)
                                recent_order = orders
                                
                                # Extract all the details
                                order_details = {
                                    'order_id': recent_order.get('order_id', 'N/A'),
                                    'shipment_id': recent_order.get('shipment_id', 'N/A'),
                                    'status': recent_order.get('display_status', {}).get('header_status', 'N/A'),
                                    'amount': recent_order.get('order_amount', 'N/A'),
                                    'date': recent_order.get('purchased_date', 'N/A'),
                                    'item_count': len(recent_order.get('item_details', [])),
                                    'items': []
                                }
                                
                                # Get all items
                                items = recent_order.get('item_details', [])
                                for item in items:
                                    order_details['items'].append({
                                        'product_name': item.get('product_name', 'N/A'),
                                        'sku_code': item.get('skucode', 'N/A'),
                                        'product_image': item.get('product_image', 'N/A')
                                    })
                                
                                overall_data.append(order_details)
                            elif re.search(r"shipped", order_status):
                                # Get the most recent order (first in the list)
                                recent_order = orders
                                
                                # Extract all the details
                                order_details = {
                                    'order_id': recent_order.get('order_id', 'N/A'),
                                    'shipment_id': recent_order.get('shipment_id', 'N/A'),
                                    'status': recent_order.get('display_status', {}).get('header_status', 'N/A'),
                                    'amount': recent_order.get('order_amount', 'N/A'),
                                    'date': recent_order.get('purchased_date', 'N/A'),
                                    'item_count': len(recent_order.get('item_details', [])),
                                    'items': []
                                }
                                
                                # Get all items
                                items = recent_order.get('item_details', [])
                                for item in items:
                                    order_details['items'].append({
                                        'product_name': item.get('product_name', 'N/A'),
                                        'sku_code': item.get('skucode', 'N/A'),
                                        'product_image': item.get('product_image', 'N/A')
                                    })
                                
                                overall_data.append(order_details)

                        if overall_data:
                            return overall_data
                    else:
                        return None
                        
                else:
                    return None
                    
            except json.JSONDecodeError:
                return None
                
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        print(e)
        return None

def get_order_details(order_id, specific_headers):
    url = "https://www.jiomart.com/api/v1/myorders/getorderdetails"
    
    # Create multipart form data
    m = MultipartEncoder(
        fields={
            'orderId': order_id,
            'shipmentId': order_id + '-01',
            'channel': 'oms',
            'shipmentType': 'ROMS'
        }
    )
    
    # Headers from the request
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        'authtoken': specific_headers.get("localStorage").get("authtoken"),
        "content-type": m.content_type,
        "origin": "https://www.jiomart.com",
        "referer": f"https://www.jiomart.com/customer/orderhistory/view/oms/{order_id}/{order_id}-01/ROMS",
        "sec-ch-ua": "\"Not.A/Brand\";v=\"99\", \"Chromium\";v=\"136\"",
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
        response = requests.post(url, headers=headers, cookies=cookies, data=m)
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")

def get_delivery_otp(order_id, specific_headers):
    url = "https://www.jiomart.com/api/v1/myorders/getorderdetails"
    
    # Create multipart form data
    m = MultipartEncoder(
        fields={
            'orderId': f'{order_id}',
            'shipmentId': f'{order_id}-01',
            'channel': 'oms',
            'shipmentType': 'ROMS'
        }
    )
    
    # Headers from the request
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9",
        'authtoken': specific_headers.get("localStorage").get("authtoken"),
        "content-type": m.content_type,
        "origin": "https://www.jiomart.com",
        "referer": "https://www.jiomart.com/customer/orderhistory/view/oms/{order_id}/{order_id}-01/ROMS",
        "sec-ch-ua": "\"Not.A/Brand\";v=\"99\", \"Chromium\";v=\"136\"",
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
        response = requests.post(url, headers=headers, cookies=cookies, data=m)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        response_data = response.json()
        
        delivery_code = response_data.get('result', {}).get('orderDetails', {}).get('delivery_code', 'N/A')
        print(type(delivery_code))
        print(delivery_code)
        if delivery_code == 'N/A':
            return False
        elif delivery_code == 'None':
            return False
        try:
            int(delivery_code)  # Check if it's numeric
            
            if len(delivery_code) != 4:
                return False
        except:
            return False
        
        return delivery_code
        
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")


def normalize(path):
    return os.path.normpath(path).rstrip("/\\").lower()


def find_profile_folder(path):
    """
    Walk upward until we reach the folder starting with 'Profile_'.
    Returns the full path to that folder.
    """
    parts = path.split(os.sep)

    for i in range(len(parts)-1, -1, -1):
        if parts[i].lower().startswith("profile_"):
            return os.sep.join(parts[:i+1])

    return path  # fallback


def remove_profile_from_orders(profile_local_data):
    url = f"{BASE_URL}/shipments/pending/read"
    payload = {"profile_local_data": profile_local_data}
    response = requests.post(url, json=payload)
    return response.json()


def is_processed_order(order_id):
    url = f"{BASE_URL}/shipments/is_processed_order"
    payload = {"order_id": order_id}
    response = requests.get(url, json=payload)
    return response.json()["is_processed"]

def set_processed(order_id):
    url = f"{BASE_URL}/shipments/set/proceed_order_id"
    payload = {"order_id": order_id}
    response = requests.get(url, json=payload)
    return response.json()


os.system("cls")
print("Accepted Link     : https://ntfy.sh/" + ntfy_accepted_topic)
print("Shipped  Link     : https://ntfy.sh/" + ntfy_shipped_topic)
print("Final Status Link : https://ntfy.sh/" + ntfy_final_status_topic + "\n\n")


def is_folder_name(value: str) -> bool:
    # If the string contains any path separator, it's a full path, not a folder name
    return os.path.sep not in value and "/" not in value and "\\" not in value



while True:
    active_orders = get_pending_list()
    if not active_orders:
        print("No active orders found. Retrying in 2 seconds...")
        time.sleep(3)
        continue

    for profile_local_data in active_orders:
        if not is_folder_name(profile_local_data): # "C:\\Users\\Test\\SLOT_01"  # False
            profile_local_data = profile_local_data + "\\local_credentials.json"
            profile_name = profile_local_data.split(os.sep)[-2]
        
        for i in range(1):
            profile_headers_data = get_profile_info(profile_local_data)
            if not profile_headers_data:
                print(f"Could not retrieve headers for profile: {profile_name}")
                break
            if profile_headers_data:
                break
                
                
        if not profile_headers_data:
            print(f"Skipping profile due to missing headers: {profile_name}")
            continue
        
        profile_headers_data = profile_headers_data[0]
        
        try:
            profile_recent_order_data = get_recent_jiomart_order(profile_headers_data, profile_local_data)
        except Exception as e:
            print(e)
            continue
        
        if not profile_recent_order_data:
            print(f"No recent orders found for profile: {profile_name}")
            continue
        
        for profile_recent_order in profile_recent_order_data:
            if is_processed_order(profile_recent_order.get("order_id")):
                continue
            try:
                order_detail = get_order_details(profile_recent_order.get("order_id"), profile_headers_data)
            except Exception as e:
                print(e)
                continue
            
            print("Checking Profile : ", profile_name)
            
            
            

            status = str(profile_recent_order.get("status", "")).lower()
            if re.search(r"ordered", status):
                print("Your Parcel Is Ordered, Waiting For Picker To Accept.")
                continue
            
            elif re.search(r"under", status):
                print("Your Parcel Is Under Processing, Waiting For Rider To Accept.")
                continue
                
            elif re.search(r"shipped", status):
                print("Your Parcel Is Shipped, Waiting For Rider To Deliver.")
                try:
                    with requests.Session() as session:
                        session.headers.update(grab_tracking_header)
                        url = f"https://track.grab.in/trackvf/{profile_recent_order.get('shipment_id')}"
                        resp = session.get(url, timeout=8)
                        resp.raise_for_status()

                        html_content = resp.text

                        if '<p class="m-error_desc m--font-bolder m--font-brand">' in html_content:
                            continue

                        rider_data = extract_rider_data(html_content)
                        
                        delivery_code = get_delivery_otp(profile_recent_order.get("order_id"), profile_headers_data)
                        
                        if not delivery_code: 
                            print("Delivery code not found, skipping notification.")
                            continue
                        
                        requested_data = {
                                "rider_checkin_selfie": rider_data.get("rider_checkin_selfie"),
                                "rider_telephone": rider_data.get("rider_telephone"),
                                "rider_name": rider_data.get("rider_name"),
                                "rider_id": rider_data.get("rider_id"),
                                
                                "profile_name": profile_name,
                                "profile_path": profile_local_data.strip(),
                                
                                "order_status": profile_recent_order.get('status'),
                                "order_amount": profile_recent_order.get('amount'),
                                "order_id": profile_recent_order.get("order_id"),
                                "total_item": profile_recent_order.get('item_count'),
                                "items": profile_recent_order.get('items'),
                                "order_date": profile_recent_order.get('date'),
                                
                                "delivery_code": delivery_code,
                                
                                "firstname": "GTX_999",
                                "cod_allowed": "COD" if order_detail.get('result').get("orderDetails").get("paymentMethod")== "COD" else "Prepaid",
                            }

                        if rider_data["rider_id"]:
                            if send_notification_for_delivery(requested_data, ntfy_shipped_topic):
                                set_processed(profile_recent_order.get("order_id"))
                                send_notification_for_delivery(requested_data, ntfy_shipped_topic + rider_data["rider_id"])
                                
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching tracking info: {e}")
                    continue

            
    time.sleep(0.5)  # check every 2 seconds










