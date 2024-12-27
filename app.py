from flask import Flask, request, jsonify
import os
from agent.core import TestAgent
from agent.device import Device, DeviceManager

app = Flask(__name__)

shared_agent = None
shared_device = None
shared_dm = None

# 初始化环境变量
os.environ["PATH"] += os.pathsep + "/opt/android/sdk/platform-tools"

@app.route('/initialize', methods=['POST'])
def initialize():
    global shared_agent, shared_device, shared_dm

    data = request.json
    missing_params = [p for p in ["app_name", "app_package", "app_launch_activity", "scenario_id"] if not data.get(p)]
    if missing_params:
        return jsonify({"error": f"Missing parameters: {', '.join(missing_params)}"}), 400

    try:
        shared_device = Device()
        base_dir = os.path.dirname(__file__)
        shared_dm = DeviceManager(device=shared_device, base_dir=base_dir)
        shared_agent = TestAgent(device_manager=shared_dm, base_dir=base_dir)
        shared_agent.initialize(
            app_name=data["app_name"],
            app_package=data["app_package"],
            app_launch_activity=data["app_launch_activity"],
            scenario_id=data["scenario_id"]
        )
        return jsonify({"message": "Agent initialized successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/step', methods=['POST'])
def step():
    global shared_agent

    if not shared_agent:
        return jsonify({"error": "Agent not initialized. Please call '/initialize' first."}), 400

    try:
        shared_agent.step()
        return jsonify({"state": shared_agent.state, "message": "Step executed."}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
