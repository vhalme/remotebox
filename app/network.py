import subprocess
import os
from .config import WG_CONFIG_PATH

IS_DEV = os.getenv("REMOTEBOX_ENV", "dev") != "prod"

def scan_wifi():
    if IS_DEV:
        return ["HomeWiFi", "Starlink", "MobileHotspot"]
    try:
        result = subprocess.run(
            ["nmcli", "device", "wifi", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        return parse_wifi(result.stdout)
    except Exception as e:
        return [f"Error: {e}"]


def connect_wifi(ssid, password):
    if IS_DEV:
        print(f"[DEV] Pretend connecting to {ssid} with password {password}")
        return True
    try:
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def set_vpn(enabled, config=None):
    if IS_DEV:
        print(f"[DEV] VPN {'enabled' if enabled else 'disabled'} with config {config}")
        return True
    try:
        if enabled and config:
            subprocess.run(["wg-quick", "up", os.path.join(WG_CONFIG_PATH, config)], check=True)
        else:
            subprocess.run(["wg-quick", "down", "wg0"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_vpn_configs():
    try:
        return [f for f in os.listdir(WG_CONFIG_PATH) if f.endswith(".conf")]
    except FileNotFoundError:
        return []

def parse_wifi(output):
    lines = output.strip().splitlines()[1:]  # Skip header
    ssids = []
    for line in lines:
        parts = line.split()
        if parts:
            ssids.append(parts[0])
    return ssids
