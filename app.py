from flask import Flask, request, jsonify, url_for
from flask_cors import CORS  # 导入 CORS 扩展
import os
from agent.core import TestAgent
from agent.device import Device, DeviceManager
import shutil


app = Flask(__name__)

CORS(app)

shared_agent: TestAgent = None
shared_device = None
shared_dm = None

STATIC_FOLDER = 'static/screenshots'
os.makedirs(STATIC_FOLDER, exist_ok=True)

# 初始化环境变量
os.environ["PATH"] += os.pathsep + "/opt/android/sdk/platform-tools"

@app.route('/initialize', methods=['POST'])
def initialize():
    global shared_agent, shared_device, shared_dm

    data = request.json
    missing_params = [p for p in ["app_name", "app_package", "app_launch_activity", "scenario_name", "scenario_description"] if not data.get(p)]
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
            scenario_name=data["scenario_name"],
            scenario_description=data["scenario_description"],
            scenario_extra_info=data["scenario_extra_info"]
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


        # 截图放到static里面，构建可访问url
        screenshot_path = shared_agent.memory.current_screenshot
        screenshot_with_bbox_path = shared_agent.memory.current_screenshot_with_bbox

        screenshot_filename = os.path.basename(screenshot_path)
        screenshot_with_bbox_filename = os.path.basename(screenshot_with_bbox_path)

        new_screenshot_path = os.path.join(STATIC_FOLDER, screenshot_filename)
        new_screenshot_with_bbox_path = os.path.join(STATIC_FOLDER, screenshot_with_bbox_filename)

        # 复制到静态文件夹
        shutil.copy(screenshot_path, new_screenshot_path)
        shutil.copy(screenshot_with_bbox_path, new_screenshot_with_bbox_path)

        if shared_agent.state == "END":
            return "GUI test ends successfully", 201
        if shared_agent.state in ["FAILED", "ERROR"]:
            return "GUI test failed", 202

        return jsonify(
            {
                "screenshot": url_for('static', filename=f'screenshots/{screenshot_filename}', _external=True),
                "screenshot_withbbox": url_for('static', filename=f'screenshots/{screenshot_with_bbox_filename}', _external=True),
                "next_actions": {
                    "intent": shared_agent.memory.performed_actions[-1].get('intent',"/"),
                    "action-type": shared_agent.memory.performed_actions[-1].get('action-type',"/"),
                    "target-widget-id": shared_agent.memory.performed_actions[-1].get("target-widget", "/").get("id", "/"),
                }
            }
        ), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
