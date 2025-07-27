import subprocess
import os
from .config import WG_CONFIG_PATH

def scan_wifi():
    try:
        print("Scanning Wi-Fi")
        result = subprocess.run(
            ["iw", "dev", "wlan0", "scan"],
            capture_output=True,
            text=True,
            check=True
        )
        print(result)
        return parse_iw_scan(result.stdout)
    except Exception as e:
        return [f"Error: {e}"]


def connect_wifi(ssid, password):
    try:
        yaml = f"""network:
                  version: 2
                  renderer: networkd
                  wifis:
                    wlan0:
                      dhcp4: true
                      dhcp6: true
                      access-points:
                        "{ssid}":
                          password: "{password}"
                """
        with open("/etc/netplan/20-wifi.yaml", "w") as f:
            f.write(yaml)

        subprocess.run(["chmod", "600", "/etc/netplan/20-wifi.yaml"], check=True)
        subprocess.run(["netplan", "apply"], check=True)

        return True
    except Exception as e:
        print(f"[ERROR] Failed to connect to Wi-Fi: {e}")
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

def parse_iw_scan(output):
    ssids = []
    current_ssid = None

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("SSID:"):
            ssid = line.split("SSID:")[1].strip()
            if ssid and ssid not in ssids:
                ssids.append(ssid)

    return ssids
  

def get_wifi_status():
    status = {
        "connected": False,
        "ssid": None,
        "ip": None
    }

    try:
        result = subprocess.run(["iw", "dev", "wlan0", "link"], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("SSID:"):
                status["ssid"] = line.split("SSID:")[1].strip()
                status["connected"] = True
    except subprocess.CalledProcessError:
        pass

    try:
        result = subprocess.run(["ip", "addr", "show", "wlan0"], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                status["ip"] = line.split()[1]
    except subprocess.CalledProcessError:
        pass

    return status

