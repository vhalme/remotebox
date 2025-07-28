import subprocess
import time
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

def get_current_network():
    result = subprocess.run(["wpa_cli", "-i", "wlan0", "list_networks"], capture_output=True, text=True)
    for line in result.stdout.strip().splitlines()[1:]:  # skip header
        parts = line.strip().split("\t")
        if len(parts) >= 4 and parts[3] == "[CURRENT]":
            return {"id": parts[0], "ssid": parts[1]}
    return None
  
def connect_wifi(ssid, password):
    try:
        print(f"[INFO] Connecting to Wi-Fi SSID: {ssid}")

        # Save current network info
        current = get_current_network()
        if current:
            print(f"[INFO] Current network: {current['ssid']} (ID {current['id']})")
        else:
            print("[INFO] No active network to revert to.")

        # Add new network
        result = subprocess.run(["wpa_cli", "-i", "wlan0", "add_network"], capture_output=True, text=True)
        net_id = result.stdout.strip()
        if not net_id.isdigit():
            raise Exception(f"Could not add network: {result.stderr.strip()}")
        print(f"[INFO] Network ID: {net_id}")

        subprocess.run(["wpa_cli", "-i", "wlan0", "set_network", net_id, "ssid", f'"{ssid}"'], check=True)
        subprocess.run(["wpa_cli", "-i", "wlan0", "set_network", net_id, "psk", f'"{password}"'], check=True)
        subprocess.run(["wpa_cli", "-i", "wlan0", "enable_network", net_id], check=True)
        subprocess.run(["wpa_cli", "-i", "wlan0", "select_network", net_id], check=True)
        subprocess.run(["wpa_cli", "-i", "wlan0", "save_config"], check=True)

        # Wait for confirmation
        wait_for_ssid_and_restart_vpn(ssid)

        print(f"[INFO] Successfully connected to {ssid}")
        return True

    except Exception as e:
        print(f"[ERROR] Wi-Fi connection failed: {e}")
        if current:
            print(f"[INFO] Reverting to previous network {current['ssid']} (ID {current['id']})...")
            subprocess.run(["wpa_cli", "-i", "wlan0", "select_network", current["id"]], check=False)
            subprocess.run(["wpa_cli", "-i", "wlan0", "enable_network", current["id"]], check=False)
            subprocess.run(["wpa_cli", "-i", "wlan0", "save_config"], check=False)
            subprocess.run(["wpa_cli", "-i", "wlan0", "remove_network", net_id], check=False)
        else:
            print("[WARN] No previous network to revert to.")
        return False

      

def wait_for_ssid_and_restart_vpn(ssid, max_attempts=5, delay=3):
    """
    Waits for the system to connect to the specified SSID.
    Once confirmed, restarts WireGuard VPN (wg0).
    """
    for attempt in range(1, max_attempts + 1):
        print(f"[INFO] Attempt {attempt}/{max_attempts} — checking connection to '{ssid}'...")
        
        try:
            result = subprocess.run(
                ["wpa_cli", "-i", "wlan0", "status"],
                capture_output=True,
                text=True,
                check=True
            )
            status_output = result.stdout

            state = None
            connected_ssid = None
            for line in status_output.splitlines():
                if line.startswith("wpa_state="):
                    state = line.split("=", 1)[1]
                elif line.startswith("ssid="):
                    connected_ssid = line.split("=", 1)[1]

            if state == "COMPLETED" and connected_ssid == ssid:
                print(f"[SUCCESS] Connected to SSID: {ssid}")
                
                # Optional: delay to allow DHCP/route to settle
                time.sleep(2)

                # Restart WireGuard VPN
                print("[INFO] Restarting WireGuard VPN (wg0)...")
                subprocess.run(["wg-quick", "down", "wg0"], check=False)
                subprocess.Popen(["wg-quick", "up", "wg0"])  # Don't block on wg0

                return True

            print(f"[INFO] State={state}, Connected SSID={connected_ssid} — not yet correct")
        
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] wpa_cli failed: {e.stderr.strip() if e.stderr else str(e)}")

        time.sleep(delay)

    raise Exception(f"[ERROR] Failed to connect to SSID '{ssid}' after {max_attempts} attempts")

  
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

