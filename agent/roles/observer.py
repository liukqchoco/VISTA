from typing import Any, Dict, List, Tuple

import cv2

from agent.device import DeviceManager
from agent.llm import LLMChatManager
from agent.logger import logger
from agent.uied.detect import WidgetDetector


class Observer:
  """
  Observer 类用于观察和捕获设备屏幕状态，并检测 GUI 中的组件。
  """

  def __init__(self, device_manager: DeviceManager, chat_manager: LLMChatManager):
    """
    初始化 Observer 类，设置设备管理器、聊天管理器和组件检测器。
    :param device_manager: DeviceManager 实例，用于控制设备操作
    :param chat_manager: LLMChatManager 实例，用于管理对话上下文
    """
    # 初始化组件检测器实例(UIED里面的)
    self.widget_detector = WidgetDetector()
    self.device_manager = device_manager
    self.chat_manager = chat_manager
    self.screen_size_fixed = False

  def capture_screenshot(self, rotate: int = 0) -> str:
    """
    捕获设备当前屏幕截图，并根据需要旋转图像。
    :param rotate: 旋转角度，默认为 0 表示不旋转
    :return: 保存截图的文件路径
    """
    screenshot_path = self.device_manager.get_screenshot()
    if rotate >= 90:
      screen = cv2.imread(screenshot_path)
      rotate_times = rotate // 90
      for _ in range(rotate_times):
        screen = cv2.rotate(screen, cv2.ROTATE_90_CLOCKWISE)
      cv2.imwrite(screenshot_path, screen)
      if rotate % 90 == 0 and rotate % 180 != 0 and not self.screen_size_fixed:
        tmp = self.device_manager.device.width
        self.device_manager.device.width = self.device_manager.device.height
        self.device_manager.device.height = tmp
        self.screen_size_fixed = True
    logger.info("Current Screenshot Captured")
    return screenshot_path

  def detect_widgets(self, screenshot_path: str) -> Tuple[str, int, Dict[str, List[Any]]]:
    """
    使用组件检测器从截图中检测 GUI 组件。
    :param screenshot_path: 截图的文件路径
    :return: 包含组件检测信息的元组，分别是带边框的截图路径、缩放比例、检测到的组件信息
    """
    logger.info("Detecting GUI Widgets")
    # 调用检测器进行组件检测，返回带边框的截图路径、缩放比例和组件信息
    screenshot_with_bbox_path, resize_ratio, elements = self.widget_detector.detect(screenshot_path)
    logger.info("Widget Detection Finished")
    return screenshot_with_bbox_path, resize_ratio, elements
