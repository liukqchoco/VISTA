import json
import time


def load_conf() -> tuple[dict[str, any], dict[str, any]]:
  """
  从指定的 JSON 配置文件中加载应用和场景列表，并将它们转换为字典形式返回。
  :return: 一个包含两个字典的元组，第一个是应用信息字典，第二个是场景信息字典
  """
  with open("config/conf.json", mode="r", encoding="utf-8") as f:
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


def load_app_and_scenario_config(app_id: str, scenario_id: str) -> dict:
  """
  从配置文件中获取指定应用和场景的配置信息。
  """
  with open("config/conf.json", mode="r", encoding="utf-8") as f:
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


def gen_timestamp() -> str:
  """
  生成当前的时间戳字符串。
  :return: 当前时间戳的字符串形式
  """
  timestamp = int(time.time())
  return str(timestamp)


def extract_json(s: str) -> dict[str, any] | None:
  """
  从字符串中提取 JSON 对象并返回。
  :param s: 包含 JSON 数据的字符串
  :return: 提取出的 JSON 对象，若无有效的 JSON 对象则返回 None
  """
  print_len_limit = min(len(s), 20)
  stack = []
  json_start_index = None
  for i, char in enumerate(s):
    if char == '{':
      stack.append(char)
      if len(stack) == 1:
        json_start_index = i
    elif char == '}':
      if not stack:
        continue
      stack.pop()
      if not stack and json_start_index is not None:
        json_string = s[json_start_index:i + 1]
        try:
          return json.loads(json_string)
        except json.JSONDecodeError:
          print(f"Error: Invalid JSON Object in ```{s[:print_len_limit]}```")
          return None
  print(f"Error: No JSON Object found in ```{s[:print_len_limit]}```")
  return None


def remove_punctuation(s: str, more_punc: list[str] | None = None) -> str:
  """
  从字符串中移除标点符号。
  :param s: 输入的字符串
  :param more_punc: 额外需要移除的标点符号列表
  :return: 移除标点后的字符串
  """
  punctuation = [',', '.', ':', ';', '_']
  if more_punc is not None:
    punctuation.extend(more_punc)
  for char in punctuation:
    s = s.replace(char, ' ')
  return s.strip()


def literally_related(s1: str, s2: str) -> bool:
  """
  判断两个字符串是否在字面上相关（逐字比较）。
  :param s1: 第一个字符串
  :param s2: 第二个字符串
  :return: 如果相关则返回 True，否则返回 False
  """
  s1 = s1.lower()
  s2 = s2.lower()
  if not s1.startswith(s2) or not s2.startswith(s1):
    return False

  if s1.strip() == "" or s2.strip() == "":
    return False

  s1_frags = s1.strip().split(" ")
  s2_frags = s2.strip().split(" ")
  if s2.startswith(s1):
    for frag in s1_frags:
      if len(frag) > 0 and frag not in s2_frags:
        return False
    return True

  if s1.startswith(s2):
    for frag in s2_frags:
      if len(frag) > 0 and frag not in s1_frags:
        return False
    return True
