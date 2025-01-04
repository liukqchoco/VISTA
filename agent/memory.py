from typing import Any, Dict, Optional

from agent.logger import logger


class Memory:
  """
  Memory 类用于存储和管理应用的相关信息，包括基本信息、执行的操作和截图等。
  """

  def __init__(self):
    self.app_name = None
    self.basic_info = None
    self.target_scenario = None
    self.performed_actions = None  # 已执行的操作列表
    self.current_elements = None
    self.suggestions = None
    # 以下都是截图路径
    self.initial_screenshot: Optional[str] = None
    self.previous_screenshot: Optional[str] = None
    self.current_screenshot: Optional[str] = None
    self.cached_screenshot: Optional[str] = None  # 缓存的截图路径
    self.previous_screenshot_with_bbox: Optional[str] = None
    self.current_screenshot_with_bbox: Optional[str] = None

    self.app_package: Optional[str] = None  # 应用包名
    self.app_launch_activity: Optional[str] = None  # 应用启动活动名称

  def add_basic_info(self, info: Dict[str, Any]) -> None:
    """set private data in test, e.g., email address, password"""
    logger.debug("Basic Scenario Information Added")
    if self.basic_info is None:
      self.basic_info = {}
    for key, value in info.items():
      self.basic_info[key] = value

  def describe_basic_info(self) -> Optional[str]:
    if self.basic_info is None or self.basic_info == {}:
      return None
    info_str = ""
    for key, value in self.basic_info.items():
      info_str += f"- {key}: {value}\n"
    return info_str[:-1]

  def cache_screenshot(self, screenshot_path: str) -> None:
    self.cached_screenshot = screenshot_path

  def save_screenshot(self, screenshot_path: str) -> None:
    """update screenshot"""
    if self.initial_screenshot is None:
      self.initial_screenshot = screenshot_path
    if self.current_screenshot is None:
      self.current_screenshot = screenshot_path
    else:
      self.previous_screenshot = self.current_screenshot
      self.current_screenshot = screenshot_path

  def save_screenshot_with_bbox(self, screenshot_path: str) -> None:
    """update screenshot with bounding box"""
    if self.current_screenshot_with_bbox is None:
      self.current_screenshot_with_bbox = screenshot_path
    else:
      self.previous_screenshot_with_bbox = self.current_screenshot_with_bbox
      self.current_screenshot_with_bbox = screenshot_path

  def add_action(self, action: Any) -> None:
    """append new action"""
    if self.performed_actions is None:
      self.performed_actions = []
    self.performed_actions.append(action)

  def remove_last_action(self) -> None:
    """remove last action"""
    if self.performed_actions is not None and len(self.performed_actions) > 0:
      self.performed_actions.pop()

  def describe_performed_actions(self) -> str:
    """stringify performed actions"""
    if self.performed_actions is None:
      return "No actions"
    actions_str = ""
    for i in range(len(self.performed_actions)):
      actions_str += f"{i + 1} - "
      actions_str += self.describe_performed_action(i) + "\n"
    return actions_str[:-1]

  def describe_performed_action(self, index: int = -1) -> str:
    action_str = ""
    action = self.performed_actions[index]
    action_type = action["action-type"]
    action_intent = action["intent"][0].lower() + action["intent"][1:]
    if action_type == "touch":
      target_widget = action["target-widget"]["description"]
      action_str += f"{action_type} the {target_widget} to {action_intent}"
    elif action_type == "input":
      target_widget = action["target-widget"]["description"]
      input_text = action["input-text"]
      action_str += (
        f"{action_type} in the {target_widget} with"
        f" text ```{input_text}``` to {action_intent}"
      )
    elif action_type == "scroll":
      action_str += f"{action_type} the screen to {action_intent}"
    elif action_type == "back":
      action_str += f"navigate {action_type} to {action_intent}"
    elif action_type == "wait":
      action_str += f"{action_intent}"
    elif action_type == "start" or action_type == "end":
      pass
    else:
      logger.error(f"Unknown action: {action_type}")
    return action_str

  def push_suggestion(self, suggestion: str) -> None:
    """append new suggestion"""
    if self.suggestions is None:
      self.suggestions = []
    self.suggestions.append(suggestion)

  def pop_suggestion(self) -> str:
    """pop last suggestion"""
    if self.suggestions is not None and len(self.suggestions) > 0:
      return self.suggestions.pop()
    return "No suggestions yet."
