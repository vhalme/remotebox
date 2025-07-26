# network_mock.py — fully mocked version for dev use

def scan_wifi():
    return ["HomeNetwork", "CoffeeShopWiFi", "MyPhoneHotspot"]

def connect_wifi(ssid, password):
    print(f"[MOCK] Connecting to SSID '{ssid}' with password '{password}'...")
    return True

def set_vpn(enabled, config=None):
    print(f"[MOCK] VPN {'ENABLED' if enabled else 'DISABLED'} with config: {config}")
    return True

def get_vpn_configs():
    return ["mock-vpn1.conf", "mock-vpn2.conf"]

def get_wifi_status():
    return {
        "connected": True,
        "ssid": "HomeNetwork",
        "ip": "192.168.1.42"
    }
