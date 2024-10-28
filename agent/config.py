import json
from typing import Any, Dict, Tuple


def load_conf() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    从指定的 JSON 配置文件中加载应用和场景列表，并将它们转换为字典形式返回。
    :return: 一个包含两个字典的元组，第一个是应用信息字典，第二个是场景信息字典
    """
    with open("agent/conf.json", mode="r", encoding="utf-8") as f:
        conf_data = json.load(f)
    app_list = conf_data["apps"]
    scenario_list = conf_data["scenarios"]
    apps = {}
    for app in app_list:
        apps[app["id"]] = app
    scenarios = {}
    for scenario in scenario_list:
        scenarios[scenario["id"]] = scenario
    return apps, scenarios


APPS, SCENARIOS = load_conf()
