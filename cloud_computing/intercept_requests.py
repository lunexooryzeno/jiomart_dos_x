from mitmproxy import http
import json


# mitmdump -s intercept_requests.py -p 9001





def patch_is_always_available(obj):
    """
    Recursively set all is_always_available keys to True in JSON object.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "is_always_available":
                obj[k] = True
            else:
                patch_is_always_available(v)
    elif isinstance(obj, list):
        for item in obj:
            patch_is_always_available(item)
            


def increase_max_order_quantity(obj, new_value=20):
    """
    Recursively set all permissible_qty keys to new_value in JSON object.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "permissible_qty":
                obj[k] = new_value
            else:
                increase_max_order_quantity(v, new_value)
    elif isinstance(obj, list):
        for item in obj:
            increase_max_order_quantity(item, new_value)
    return obj



def response(flow: http.HTTPFlow):
    # target only the specific endpoint
    if "mst/rest/v1/5/cart/get" in flow.request.url:
        try:
            # parse JSON response
            data = json.loads(flow.response.text)
            
            # patch all is_always_available flags
            patch_is_always_available(data)
            
            # replace response body with modified JSON
            flow.response.text = json.dumps(data)
            
            print(f"[+] Patched response for: {flow.request.url}")
        except Exception as e:
            print(f"[!] Failed to modify response: {e}")
            
    elif "hcat/rest/v1/customer/max-order-quantity" in flow.request.url:
        try:
            # parse JSON response
            data = json.loads(flow.response.text)
            
            # patch all is_always_available flags
            increase_max_order_quantity(data)
            
            # replace response body with modified JSON
            flow.response.text = json.dumps(data)
            
            print(f"[+] Patched response for: {flow.request.url}")
        except Exception as e:
            print(f"[!] Failed to modify response: {e}")
