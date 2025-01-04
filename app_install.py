import os
import subprocess
from typing import Optional, Union

from agent.config import APPS


def install_app(apk_path: str) -> None:
  cmd = f"adb install {apk_path}"
  subprocess.run(cmd, shell=True)


def install_from_config(
        app_id: Union[int, str],
        project_base: Optional[str] = os.getcwd()
) -> None:
  if isinstance(app_id, int):
    app_id = f"A{app_id}"
  apk_path = APPS[app_id]["apk-path"]
  if project_base is not None:
    apk_path = f"{project_base}/data/apk/{apk_path}"
  install_app(apk_path)


if __name__ == "__main__":
  install_from_config(1)
