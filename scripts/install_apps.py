import os
import subprocess

from agent.utils import load_conf


def _install_app(apk_path: str) -> None:
  cmd = f"adb install {apk_path}"
  subprocess.run(cmd, shell=True)


def install_from_config(
        app_id: int | str,
        project_base: str | None = os.getcwd()
) -> None:
  """
  安装指定 ID 的应用至待测安卓设备。
  :param app_id: 应用 ID
  :param project_base: 项目根目录，默认为当前工作目录
  """
  if isinstance(app_id, int):
    app_id = f"A{app_id}"
  apps, _ = load_conf()
  apk_path = apps[app_id]["apk-path"]
  if project_base is not None:
    apk_path = f"{project_base}/data/apk/{apk_path}"
  _install_app(apk_path)


if __name__ == "__main__":
  install_from_config(1)
