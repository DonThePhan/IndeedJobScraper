import requests

proxy_list = [
    'gate.smartproxy.com:10001:sp5hlp83m2:xJ0sy7CwKjex~8d2St'
]

for proxy in proxy_list:
    # Extract details
    parts = proxy.split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        formatted_proxy = f"http://{user}:{password}@{host}:{port}"

        proxies = {
            'http': formatted_proxy,
            'https': formatted_proxy,
        }

        try:
            response = requests.get('http://www.google.com', proxies=proxies, timeout=10)
            print(f"Proxy works! Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Proxy test failed: {e}")
    else:
        print("Invalid proxy format")
