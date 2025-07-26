import time, os
from flask import Blueprint, render_template, request, jsonify
from . import state
if os.getenv("REMOTEBOX_ENV") == "prod":
    from . import network
else:
    from . import network_mock as network

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    wifi_list = network.scan_wifi()
    current = network.get_wifi_status()
    current_ssid = current["ssid"] if current["connected"] else None
    return render_template("index.html", wifi_list=wifi_list, current_ssid=current_ssid)

@bp.route("/connect_wifi", methods=["POST"])
def connect_wifi():
    ssid = request.form["ssid"]
    password = request.form["password"]
    network.connect_wifi(ssid, password)

    time.sleep(4)  # Wait for netplan to apply

    status = network.get_wifi_status()

    if status["connected"] and status["ssid"] == ssid:
        msg = f"""
        <div id='wifi-connection-status'>
          <h2>Current Wi-Fi Status</h2>
          <p><strong>Status:</strong> Connected</p>
          <p><strong>SSID:</strong> {status['ssid']} | <strong>IP:</strong> {status['ip']}</p>
        </div>
        """
    else:
        msg = f"""
        <div id='wifi-connection-status'>
          <h2>Current Wi-Fi Status</h2>
          <p><strong>Status:</strong> ❌ Failed to connect to {ssid}</p>
        </div>
        """

    return msg


@bp.route("/toggle_vpn", methods=["POST"])
def toggle_vpn():
    enabled = request.form["enabled"] == "true"
    config = request.form.get("config")
    success = network.set_vpn(enabled, config)
    return jsonify({"success": success})
  

@bp.route("/wifi_status")
def wifi_status():
    return jsonify(network.get_wifi_status())

