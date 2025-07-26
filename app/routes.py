from flask import Blueprint, render_template, request, jsonify
from . import network, state

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    wifi_list = network.scan_wifi()
    vpn_configs = network.get_vpn_configs()
    current_state = state.load_settings()
    return render_template("index.html", wifi_list=wifi_list, vpn_configs=vpn_configs, state=current_state)

@bp.route("/connect_wifi", methods=["POST"])
def connect_wifi():
    ssid = request.form["ssid"]
    password = request.form["password"]
    success = network.connect_wifi(ssid, password)
    return jsonify({"success": success})

@bp.route("/toggle_vpn", methods=["POST"])
def toggle_vpn():
    enabled = request.form["enabled"] == "true"
    config = request.form.get("config")
    success = network.set_vpn(enabled, config)
    return jsonify({"success": success})
