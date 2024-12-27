import os

from flask import jsonify

from agent.core import TestAgent
from agent.device import Device, DeviceManager


if __name__ == "__main__":
    # 将 Android SDK 的 platform-tools 路径（比如 adb 等工具所在位置）加入到系统的 PATH 环境变量中
    # 这样，脚本在后续执行过程中可以调用 Android 的工具如 adb 来与 Android 设备交互。
    os.environ["PATH"] += ":/opt/android/sdk/platform-tools"

    device = Device()
    # 获取当前脚本所在路径
    base_dir = os.path.dirname(__file__)
    dm = DeviceManager(device=device, base_dir=base_dir)
    agent = TestAgent(device_manager=dm, base_dir=base_dir)
    agent.initialize(app_name="DeepL Translator", app_package="com.deepl.mobiletranslator", app_launch_activity=".MainActivity", scenario_id="S5")  # 113.115 wrong

    print("Please open the app and direct it to the initial page of the scenario.")
    input("Press enter to start the test...")

    while agent.state != "FAILED" and agent.state != "END" and agent.state != "ERROR":
        agent.step()
        if agent.state == "END":
            a = jsonify({"message": "GUI testing ends successfully."}), 200
        if agent.state == "FAILED" and agent.state == "ERROR":
            a = jsonify({"message": "Sorry, GUI testing failed. Please try again."}), 500

        a = jsonify(
            {
                "screenshot": agent.memory.current_screenshot,
                "screenshot_withbbox": agent.memory.current_screenshot_with_bbox,
                "next_actions": jsonify(
                    {
                        "intent": agent.memory.performed_actions[-1]['intent'],
                        "action-type": agent.memory.performed_actions[-1]['action-type'],
                        "target-widget-id": agent.memory.performed_actions[-1]['target-widget']['id'],
                    }
                )
            })


