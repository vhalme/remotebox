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
        print("Scan complete")
        return parse_iw_scan(result.stdout)
    except Exception as e:
        return [f"Error: {e}"]


import subprocess
import time
import os
import shutil

def connect_wifi(ssid, password):
    main_yaml_path = "/etc/netplan/20-wifi.yaml"
    backup_yaml_path = "/etc/netplan/20-wifi.yaml.bak"

    new_yaml = f"""network:
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

    try:
        print(f'Replace config to {ssid}...')
        # Backup existing config
        if os.path.exists(main_yaml_path):
            shutil.copy(main_yaml_path, backup_yaml_path)
            os.remove(main_yaml_path)

        # Write temporary config
        with open(main_yaml_path, "w") as f:
            f.write(new_yaml)

        subprocess.run(["chmod", "600", main_yaml_path], check=True)
        
        print(f'Apply config...')
        subprocess.run(["netplan", "apply"], check=True)

        print(f'Wait 5s')
        time.sleep(5)

        wait_for_ssid_and_restart_vpn(ssid, 3, 5)

    except Exception as e:
        print(f"[ERROR] Wi-Fi connection failed: {e}")
        # Restore previous config if we had one
        if os.path.exists(backup_yaml_path):
            os.remove(main_yaml_path)
            shutil.copy(backup_yaml_path, main_yaml_path)
            subprocess.run(["netplan", "apply"], check=True)
            time.sleep(6)
            subprocess.run(["wg-quick", "down", "wg0"])
            subprocess.run(["wg-quick", "up", "wg0"])
        return False


def wait_for_ssid_and_restart_vpn(ssid, max_attempts=3, delay=5):
    for attempt in range(1, max_attempts + 1):
        result = subprocess.run(
            ["iw", "dev", "wlan0", "link"],
            capture_output=True,
            text=True
        )

        print(f"[Attempt {attempt}] Connection check: {result.stdout.strip()} [{result.stderr.strip()}]")

        if f'SSID: {ssid}' in result.stdout:
            print(f"[INFO] Initial status check successful, waiting 6 s.")
            time.sleep(6)
            result = subprocess.run(
              ["iw", "dev", "wlan0", "link"],
              capture_output=True,
              text=True
            )
            if f'SSID: {ssid}' in result.stdout:
              print(f"[INFO] Successfully connected to {ssid}. Restarting WireGuard...")
              subprocess.run(["wg-quick", "down", "wg0"])
              subprocess.Popen(["wg-quick", "up", "wg0"])  # use Popen to avoid blocking Flask
              return True
            else:
              raise Exception(f"[ERROR] Failed to connect, wrong password")
        if attempt < max_attempts:
            print(f"[INFO] Not connected to {ssid}, retrying in {delay} seconds...")
            time.sleep(delay)

    raise Exception(f"[ERROR] Failed to connect to {ssid} after {max_attempts} attempts")
  
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

