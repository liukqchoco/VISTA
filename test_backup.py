import json
import os

import yaml

from agent.core import TestAgent
from agent.device import Device, DeviceManager


def get_app_and_scenario_config(app_id: str, scenario_id: str) -> dict:
  with open("agent/conf.json", "r") as f:
    configs = json.load(f)
  app_config = [x for x in configs["apps"] if x["id"] == app_id]
  if len(app_config) == 0:
    raise ValueError(f"App config with id {app_id} not found.")
  scenario_config = [x for x in configs["scenarios"] if x["id"] == scenario_id]
  if len(scenario_config) == 0:
    raise ValueError(f"Scenario config with id {scenario_id} not found.")
  return {
    "app_name": app_config[0]["name"],
    "app_package": app_config[0]["package"],
    "app_launch_activity": app_config[0]["launch-activity"],
    "scenario_name": scenario_config[0]["name"],
    "scenario_description": scenario_config[0]["description"],
    "scenario_extra_info": scenario_config[0]["extra-info"],
  }


if __name__ == "__main__":
  with open("config/application.yml", "r") as f:
    config = yaml.safe_load(f)["test"]
  os.environ["PATH"] += os.pathsep + config["adb_path"]

  device = Device()
  # 获取当前脚本所在路径
  base_dir = os.path.dirname(__file__)
  dm = DeviceManager(device=device, base_dir=base_dir)
  agent = TestAgent(device_manager=dm, base_dir=base_dir)

  agent.initialize(**get_app_and_scenario_config(config["app_id"], config["scenario_id"]))  # 113.115 wrong

  print("Please open the app and direct it to the initial page of the scenario.")
  input("Press enter to start the test...")

  while agent.state != "FAILED" and agent.state != "END" and agent.state != "ERROR":
    agent.step()
