import os

import yaml

from agent.core import TestAgent
from agent.device import Device, DeviceManager
from agent.utils import load_app_and_scenario_config


def main():
  """
  独立测试后端的入口。
  """
  with open("config/application.yml", "r") as f:
    config = yaml.safe_load(f)["test"]
  os.environ["PATH"] += os.pathsep + config["adb_path"]

  device = Device()
  base_dir = os.path.dirname(__file__)
  dm = DeviceManager(device=device, base_dir=base_dir)
  agent = TestAgent(device_manager=dm, base_dir=base_dir)

  agent.initialize(**load_app_and_scenario_config(config["app_id"], config["scenario_id"]))  # 113.115 wrong

  print("Please open the app and direct it to the initial page of the scenario.")
  input("Press enter to start the test...")

  while agent.state != "FAILED" and agent.state != "END" and agent.state != "ERROR":
    agent.step()


if __name__ == "__main__":
  main()
