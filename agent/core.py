from typing import Any, Optional

from agent.device import DeviceManager
from agent.llm import LLMChatManager
from agent.logger import logger
from agent.memory import Memory
from agent.roles.decider import ActionDecider
from agent.roles.executor import ActionExecutor
from agent.roles.observer import Observer
from agent.roles.perceiver import Perceiver
from agent.roles.recorder import TestRecorder
from agent.roles.supervisor import TestSupervisor


class TestAgent:
  """
  TestAgent 类用于自动化测试流程，包括应用初始化、执行步骤控制、错误处理等操作。
  """

  def __init__(self, device_manager: DeviceManager, base_dir: str):
    """
    初始化 TestAgent 实例，设置所有角色和状态。
    :param device_manager: DeviceManager 实例，用于控制设备操作
    :param base_dir: 基础目录路径，用于存储数据
    """
    self.state = "UNINITIALIZED"
    self.app = None
    self.scenario = None
    self.llm = LLMChatManager()
    self.device_manager = device_manager
    self.observer = Observer(device_manager, self.llm)
    self.perceiver = Perceiver(self.llm)
    self.decider = ActionDecider(self.llm)
    self.recorder = TestRecorder(self.llm, base_dir)
    self.executor = ActionExecutor(device_manager, self.recorder)
    self.supervisor = TestSupervisor(self.llm)
    self.memory = Memory()
    self.loading_check_fail_count = 0
    self.match_error_count = 0
    self.decide_error_count = 0
    self.rotate_angle = 0
    self.issue_table = [
      "",
      "error occurred in matching target widget with its number",  # 1
      "necessary preliminary action was neglected causing the app to not respond correctly",  # 2
      "the selected action triggered the bug of the app",  # 3
      "the selected action doesn't correspond to the task scenario"  # 4
    ]

  def initialize(self,
                 app_name: str,
                 app_package: str,
                 app_launch_activity: str,
                 scenario_name: str,
                 scenario_description: str,
                 scenario_extra_info: dict = None,
                 rotate_angle: int = 0
                 ):
    """
    初始化 TestAgent，根据给定的应用和场景 ID 设置目标应用和场景，并启动应用。
    """
    if self.state == "UNINITIALIZED":
      logger.info("Initializing TestAgent")
      self.state = "INITIALIZED"
      # self.app: Dict = APPS[app_id]
      self.app = {"id": "-1"}
      self.scenario = {"id": "-1"}
      # self.scenario: Dict = SCENARIOS[scenario_id]
      self.rotate_angle = rotate_angle
      self.executor.rotate_angle = rotate_angle
      self.memory.app_name = app_name
      self.memory.app_package = app_package
      self.memory.app_launch_activity = app_launch_activity
      self.memory.target_scenario = scenario_description
      if scenario_extra_info != None:
        self.memory.add_basic_info(scenario_extra_info)
      self.device_manager.launch_app(
        self.memory.app_package,
        self.memory.app_launch_activity,
      )
    else:
      logger.warning("TestAgent has already been initialized")

  def step(self) -> Optional[Any]:
    """
    控制 TestAgent 的步骤执行流程，根据当前状态决定下一步操作。
    :return: 如果流程结束返回 None，否则继续执行
    """
    if self.state == "UNINITIALIZED":
      _continue = self._state_uninitialized()
      if not _continue:
        return None

    if self.state == "EXECUTING":  # 3
      _continue = self._state_executing()
      if not _continue:
        return None

    screenshot_path = self.observer.capture_screenshot(self.rotate_angle)
    self.memory.cache_screenshot(screenshot_path)

    if self.state == "INITIALIZED":  # 1
      _continue = self._state_initialized()
      if not _continue:
        return None

    if self.state == "LOAD-CHECKING":  # 4
      _continue = self._state_load_checking()
      if not _continue:
        return None

    if self.state == "EFFECT-CHECKING":  # 5
      _continue = self._state_effect_checking()
      if not _continue:
        return None

    if self.state == "END-CHECKING":  # 6
      _continue = self._state_end_checking()
      if not _continue:
        return None

    if self.state == "CORRECTING":  # 5.5
      _continue = self._state_correcting()
      if not _continue:
        return None

    if self.state == "OBSERVING":  # 2
      _continue = self._state_observing()
      if not _continue:
        return None

    return None

  def report_self(self):
    """
    输出当前状态的报告，并在失败或结束时生成测试脚本。
    """
    meta_info = {
      "resize-ratio": self.device_manager.resize_ratio,
      "device-width": self.device_manager.device.width,
      "device-height": self.device_manager.device.height,
    }
    if self.state == "FAILED" or self.state == "ERROR":
      script_path = self.recorder.scripted(
        self.app["id"],
        self.scenario["id"],
        addition=meta_info,
        failed=True,
        full_chat=True,
      )
      logger.info(f"Script Generated: {script_path}")
    elif self.state == "END":
      script_path = self.recorder.scripted(
        self.app["id"],
        self.scenario["id"],
        addition=meta_info,
        full_chat=True,
      )
      logger.info(f"Script Generated: {script_path}")
    else:
      logger.info(f"Agent State: {self.state}. TestING...")

  def _state_uninitialized(self) -> bool:
    """
    处理 UNINITIALIZED 状态，返回 False 表示初始化失败。
    """
    logger.waring(f"TestAgent State: {self.state}")
    return False

  def _state_initialized(self) -> bool:
    """
    处理 INITIALIZED 状态，转移到 OBSERVING 状态。
    """
    self.state = "OBSERVING"
    return True

  def _state_executing(self) -> bool:
    """
    执行已决定的操作，并记录操作，转移到 LOAD-CHECKING 状态。
    """
    # call function to execute decided action and record the action
    self.executor.execute(self.memory)
    self.state = "LOAD-CHECKING"
    return True

  def _state_load_checking(self) -> bool:
    """
    检查页面是否仍在加载，处理加载失败或成功的逻辑。
    """
    if self.loading_check_fail_count > 2:
      self.loading_check_fail_count = 0
      self.state = "EFFECT-CHECKING"
      return True
    is_loading = self.supervisor.check_loading(self.memory)
    if is_loading is None:
      self.state = "ERROR"
      self.report_self()
      return False
    if is_loading:
      self.loading_check_fail_count += 1
      wait_action = {"action-type": "wait", "intent": "wait for loading"}
      self.memory.add_action(wait_action)
      self.executor.execute(self.memory)
      self.memory.remove_last_action()
      return False
    else:
      self.loading_check_fail_count = 0
      self.state = "EFFECT-CHECKING"
      return True

  def _state_effect_checking(self) -> bool:
    """
    检查页面的效果变化，处理需要返回的情况，或转移到下一状态。
    """
    valid, need_back = self.supervisor.check_effect(self.memory)
    if valid is None:
      self.state = "ERROR"
      self.report_self()
      return False
    if not valid:
      if need_back:
        back_action = {"action-type": "back", "intent": "NEED-BACK"}
        self.memory.add_action(back_action)
        self.executor.execute(self.memory)
      self.state = "CORRECTING"
    else:
      self.match_error_count = 0
      self.decide_error_count = 0
      self.state = "END-CHECKING"
    return True

  def _state_end_checking(self) -> bool:
    """
    检查测试是否已完成，生成报告并结束。
    """
    test_end = self.supervisor.check_end(self.memory)
    if test_end is None:
      self.state = "ERROR"
      self.report_self()
      return False
    if test_end:
      self.state = "END"
      logger.info("Test Finished")
      self.report_self()
      return False
    else:
      self.state = "OBSERVING"
      return True

  def _state_observing(self) -> bool:
    """
    观察当前屏幕内容，检测元素，确定下一步操作并准备执行。
    """
    self.memory.save_screenshot(self.memory.cached_screenshot)
    self.memory.cached_screenshot = None
    # 1. send original image and prompt to llm, understand the scenario
    action = self.perceiver.understanding(self.memory)
    # 2. detect widgets in original image, generate marked image
    screenshot_path = self.memory.current_screenshot
    screenshot_with_bbox_path, resize_ratio, elements = self.observer.detect_widgets(screenshot_path)
    self.memory.save_screenshot_with_bbox(screenshot_with_bbox_path)
    self.memory.current_elements = elements
    # 3. decide concrete action by widget matching or marked image analysis
    action = self.decider.next_action(self.memory, self.perceiver, action, 0)
    self.memory.add_action(action)
    if action is None:
      self.state = "ERROR"
      self.report_self()
      return False
    # record resize ratio
    if self.device_manager.resize_ratio is None:
      self.device_manager.set_resize_ratio(resize_ratio)
    self.state = "EXECUTING"
    return False

  def _state_correcting(self) -> bool:
    """
    修正测试中出现的错误，根据问题类型重新执行或调整操作。
    """
    last_action = self.memory.performed_actions[-1]
    if last_action["action-type"] == "back" and last_action["intent"] == "NEED-BACK":
      self.memory.remove_last_action()
      need_back = True
    else:
      need_back = False

    situation_number = 1 if self.match_error_count > 0 \
      else self.decider.issue_feedback(need_back)
    if situation_number is None:
      self.state = "ERROR"
      self.report_self()
      return False
    elif situation_number == 1:
      self.match_error_count += 1
      if self.match_error_count > 2:
        self.state = "FAILED"
        self.report_self()
        return False
      action = self.decider.rematch_next_action(self.memory)
    else:
      situation = self.issue_table[situation_number]
      self.decide_error_count += 1
      if self.decide_error_count > 2:
        self.state = "FAILED"
        self.report_self()
        return False
      action = self.perceiver.understanding(self.memory, correcting=True, situation=situation)
      if action is not None:
        action = self.decider.confirm_next_action(self.memory, action)

    if action is None:
      self.state = "ERROR"
      self.report_self()
      return False
    self.memory.remove_last_action()
    self.memory.add_action(action)
    self.state = "EXECUTING"
    return False
