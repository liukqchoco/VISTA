from typing import Any, Dict, Optional

from agent.llm import LLMChatManager
from agent.logger import logger
from agent.memory import Memory
from agent.prompt.decider import (
  user_prompt_rematch_widget,
  user_prompt_confirm_input_action,
  user_prompt_confirm_touch_action,
  user_prompt_confirm_next_action,
  user_prompt_fix_location,
  user_prompt_analyze_situation,
  user_prompt_analyze_missing_widget
)
from agent.utils import (
  extract_json,
  remove_punctuation,
  literally_related
)


class ActionDecider:
  """
  ActionDecider 类负责根据用户交互和当前应用状态，
  通过大语言模型 (LLM) 决策下一步操作。
  """

  def __init__(self, chat_manager: LLMChatManager):
    """
    初始化 ActionDecider 类，设置聊天管理器和默认的决策阶段。
    :param chat_manager: LLMChatManager 实例，用于管理对话
    """
    self.chat_manager = chat_manager
    self.stage = "action-decision"
    self.enable_text_match = True  # 启用文本匹配功能

  def next_action(
          self,
          memory: Memory,
          action: Dict[str, Any],
          repeat_times: int = 0,
  ) -> Optional[Dict[str, Any]]:
    """
    确认或修正下一步操作，支持文本和视觉匹配。
    :param memory: Memory 实例，包含应用的当前状态和历史操作
    :param action: 预定的操作
    :param repeat_times: 确认次数，默认 0
    :return: 确认后的操作字典或 None
    """
    if repeat_times > 2:
      logger.error("Repeat Confirming Too Many Times")
      return None

    # 直接返回无需目标组件的操作，如 'back' 和 'scroll'
    if action["action-type"] == "back" or action["action-type"] == "scroll":
      logger.info(f"Action {action['action-type']} requires no target widget")
      action["target-widget"] = None
      return action

    # action-type: input / touch
    # 尝试通过文本匹配目标组件
    matched_element = None
    if action.get("target-widget") is not None and self.enable_text_match:
      for element in memory.current_elements:
        if element.get("text_content") is not None:
          ocr_text = element.get("text_content").lower()
          ocr_text = remove_punctuation(ocr_text)
          wid_desc = action["target-widget"].lower()
          wid_desc = remove_punctuation(wid_desc)
          if literally_related(ocr_text, wid_desc):
            matched_element = element
            break
    if matched_element is not None:
      # 成功匹配到目标组件
      matched_element["description"] = action["target-widget"]
      action["target-widget"] = matched_element
      logger.info("Target Widget Found By Text Matching")
      # 添加匹配上下文
      user_prompt = user_prompt_confirm_next_action()
      user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
      self.chat_manager.context_pool[self.stage].append_user_message(user_message)
      self.chat_manager.context_pool[self.stage].append_assistant_message(
        f"Widget: {{\"target-widget-number\": {matched_element['id']}}}"
      )
      # 确认输入操作的位置
      if action["action-type"] == "input":
        w_id = action["target-widget"]["id"]
        user_prompt = user_prompt_confirm_input_action(w_id)
        user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
        self.chat_manager.context_pool["temporary"].refresh()
        self.chat_manager.context_pool["temporary"].copy_from(
          self.chat_manager.context_pool[self.stage]
        )

        logger.info("Confirming Input Location")
        response, p_usage, r_usage = self.chat_manager.get_response(
          stage="temporary",
          model="gpt-4-vision-preview",
          prompt=user_message,
        )
        logger.info("Confirm Result Received")
        logger.debug(f"Response: ```{response}```")

        # 从回复中提取位置信息
        position = extract_json(response)
        if position is None \
                or position.get("position") is None \
                or position["position"] not in ("up", "down", "left", "right", "self"):
          logger.warning("No Valid Position Confirmed & Use Default")
          action["position"] = "self"
        else:
          action["position"] = position["position"]
      return action

    # 尝试通过视觉识别匹配目标组件
    user_prompt = user_prompt_confirm_next_action()
    user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
    logger.info("Querying Target Widget")
    response, p_usage, r_usage = self.chat_manager.get_response(
      stage=self.stage,
      model="gpt-4-vision-preview",
      prompt=user_message,
    )
    logger.info("Query Result Received")
    logger.info(f"Token Cost: {p_usage} + {r_usage}")
    logger.debug(f"Response: ```{response}```")

    # 从回复中提取组件编号
    widget = extract_json(response)
    if widget is None or widget.get("target-widget-number") is None:
      logger.error("No Widget Number Found")
      return None

    # no widget matched, predict location based on existing widgets
    if int(widget["target-widget-number"]) == -1:
      logger.warning("No Target Widget Detected")
      user_message = user_prompt_analyze_missing_widget()
      self.chat_manager.context_pool["temporary"].refresh()
      self.chat_manager.context_pool["temporary"].copy_from(
        self.chat_manager.context_pool[self.stage]
      )
      logger.info("Analyzing Missing Target Widget")
      response, p_usage, r_usage = self.chat_manager.get_response(
        stage="temporary",
        model="gpt-4-vision-preview",
        prompt=user_message,
      )
      logger.info("Analysis Result Received")
      logger.info(f"Token Cost: {p_usage} + {r_usage}")
      logger.debug(f"Response: ```{response}```")
      option = extract_json(response)
      if option is None \
              or option.get("option-number") is None \
              or option["option-number"] not in (1, 2):
        logger.error("No Valid Option Found")
        return None
      option_num = option['option-number']
      logger.info(f"Option Number Extracted: {option_num}")
      if option_num == 1:
        action = self.next_action(
          memory,
          correcting=True,
          situation=(
            "necessary preliminary action was neglected"
            " causing the app to not respond correctly"
          )
        )
        return self.confirm_next_action(memory, action, repeat_times + 1)

      if action["action-type"] == "input":
        user_message = user_prompt_confirm_input_action()
      elif action["action-type"] == "touch":
        user_message = user_prompt_confirm_touch_action()
      else:
        logger.error(f"Invalid Action Type: {action['action-type']}")
        return None
      # confirm where to touch
      logger.info("Querying Possible Location")
      response, p_usage, r_usage = self.chat_manager.get_response(
        stage="action-decision",
        model="gpt-4-vision-preview",
        prompt=user_message,
      )
      logger.info("Possible Location Received")
      logger.info(f"Token Cost: {p_usage} + {r_usage}")
      logger.debug(f"Response: ```{response}```")
      # extract location description
      location = extract_json(response)
      if location is None \
              or location.get("position") is None \
              or location.get("widget-number") is None \
              or location["position"] not in ("up", "down", "left", "right"):
        logger.error("No Valid Location Clarified")
        return None
      # get matched widget in location description
      for element in memory.current_elements:
        if element["id"] == int(location["widget-number"]):
          action["target-widget"] = element
          action["target-widget"]["id"] = -1
          if action["action-type"] == "input":
            action["target-widget"]["description"] = "blank_field"
          else:
            action["target-widget"]["description"] = "undetected_button"
          break
      action["position"] = location["position"]
      return action

    # widget matched, get matched widget
    for element in memory.current_elements:
      if element["id"] == int(widget["target-widget-number"]):
        if action.get("target-widget") is not None:
          element["description"] = action["target-widget"]
        else:
          element["description"] = "target widget"
        action["target-widget"] = element
        logger.info("Target Widget Found By Vision")
        break
    # confirm touch position for input action
    if action["action-type"] == "input":
      w_id = action["target-widget"]["id"]
      user_prompt = user_prompt_confirm_input_action(w_id)
      user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
      self.chat_manager.context_pool["temporary"].refresh()
      self.chat_manager.context_pool["temporary"].copy_from(
        self.chat_manager.context_pool[self.stage]
      )

      logger.info("Confirming Input Location")
      response, p_usage, r_usage = self.chat_manager.get_response(
        stage="temporary",
        model="gpt-4-vision-preview",
        prompt=user_message,
      )
      logger.info("Confirm Result Received")
      logger.info(f"Token Cost: {p_usage} + {r_usage}")
      logger.debug(f"Response: ```{response}```")

      # extract position description
      position = extract_json(response)
      if position is None \
              or position.get("position") is None \
              or position["position"] not in ("up", "down", "left", "right", "self"):
        logger.warning("No Valid Position Confirmed & Use Default")
        action["position"] = "self"
      else:
        action["position"] = position["position"]
    return action

  def rematch_next_action(self, memory: Memory) -> Optional[Dict[str, Any]]:
    """
    尝试重新匹配目标组件，并根据视觉或文本结果进行决策调整。
    :param memory: Memory 实例，包含应用的当前状态和历史操作
    :return: 确认后的操作字典或 None
    """
    # 获取最近执行的操作
    action = memory.performed_actions[-1]
    if action["target-widget"]["id"] != -1:
      # 如果已有有效的目标组件 ID，则重新匹配
      user_message = user_prompt_rematch_widget()

      suggestion = memory.pop_suggestion()
      if suggestion is not None:
        user_message += (f"\n\nBelow is the suggestion from the last decision"
                         f" that may help you better match the target widget:\n\n{suggestion}")

      logger.info("Rematching Target Widget")
      response, p_usage, r_usage = self.chat_manager.get_response(
        stage=self.stage,
        model="gpt-4-vision-preview",
        prompt=user_message,
      )
      logger.info("Rematch Result Received")
      logger.info(f"Token Cost: {p_usage} + {r_usage}")
      logger.debug(f"Response: ```{response}```")

      widget = extract_json(response)
      if widget is None or widget.get("target-widget-number") is None:
        logger.error("No Widget Number Found")
        return None

      # 没有匹配到组件，尝试通过视觉重新预测位置
      if int(widget["target-widget-number"]) == -1:
        logger.warning("No Widget Rematched")
        if action["action-type"] == "input":
          user_message = user_prompt_confirm_input_action()
        elif action["action-type"] == "touch":
          user_message = user_prompt_confirm_touch_action()
        else:
          logger.error(f"Invalid Action Type: {action['action-type']}")
          return None
        # confirm where to touch
        logger.info("Querying Possible Location")
        response, p_usage, r_usage = self.chat_manager.get_response(
          stage="action-decision",
          model="gpt-4-vision-preview",
          prompt=user_message,
        )
        logger.info("Possible Location Received")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")
        # extract location description
        location = extract_json(response)
        if location is None \
                or location.get("position") is None \
                or location.get("widget-number") is None \
                or location["position"] not in ("up", "down", "left", "right"):
          logger.error("No Valid Location Clarified")
          return None
        # get matched widget in location description
        for element in memory.current_elements:
          if element["id"] == int(location["widget-number"]):
            action["target-widget"] = element
            action["target-widget"]["id"] = -1
            if action["action-type"] == "input":
              action["target-widget"]["description"] = "blank_field"
            else:
              action["target-widget"]["description"] = "undetected_button"
            break
        action["position"] = location["position"]
        return action

      # 成功匹配到组件
      for element in memory.current_elements:
        if element["id"] == int(widget["target-widget-number"]):
          if action["target-widget"].get("description") is not None:
            widget_desc = action["target-widget"]["description"]
            action["target-widget"] = element
            action["target-widget"]["description"] = widget_desc
          else:
            action["target-widget"] = element
            action["target-widget"]["description"] = "target widget"
          logger.info("Target Widget Found By Vision")
          break

      # confirm touch position for input action
      if action["action-type"] == "input":
        w_id = action["target-widget"]["id"]
        user_prompt = user_prompt_confirm_input_action(w_id)
        user_message = {"text": user_prompt, "image": memory.current_screenshot_with_bbox}
        self.chat_manager.context_pool["temporary"].refresh()
        self.chat_manager.context_pool["temporary"].copy_from(
          self.chat_manager.context_pool[self.stage]
        )

        logger.info("Confirming Input Location")
        response, p_usage, r_usage = self.chat_manager.get_response(
          stage="temporary",
          model="gpt-4-vision-preview",
          prompt=user_message,
        )
        logger.info("Confirm Result Received")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        position = extract_json(response)
        if position is None \
                or position.get("position") is None \
                or position["position"] not in ("up", "down", "left", "right", "self"):
          logger.warning("No Valid Position Confirmed & Use Default")
          action["position"] = "self"
        else:
          action["position"] = position["position"]
      return action
    else:
      # 如果没有有效的组件 ID，则重新预测位置
      user_message = user_prompt_fix_location()

      suggestion = memory.pop_suggestion()
      user_message += (f"\n\nBelow is the suggestion from the last decision"
                       f" that may help you better navigate:\n\n{suggestion}")

      logger.info("Re-predicting Target Widget Location")
      response, p_usage, r_usage = self.chat_manager.get_response(
        stage=self.stage,
        model="gpt-4-vision-preview",
        prompt=user_message,
      )
      logger.info("Prediction Result Received")
      logger.info(f"Token Cost: {p_usage} + {r_usage}")
      logger.debug(f"Response: ```{response}```")

      location = extract_json(response)
      if location is None \
              or location.get("position") is None \
              or location.get("widget-number") is None \
              or location["position"] not in ("up", "down", "left", "right"):
        logger.error("No Valid Location Clarified")
        return None

      for element in memory.current_elements:
        if element["id"] == int(location["widget-number"]):
          action["target-widget"] = element
          action["target-widget"]["id"] = -1
          if action["action-type"] == "input":
            action["target-widget"]["description"] = "blank_field"
          else:
            action["target-widget"]["description"] = "undetected_button"
          break
      action["position"] = location["position"]
      return action

  def issue_feedback(self, need_back: bool) -> Optional[int]:
    """
    获取操作反馈，分析执行结果。
    :param need_back: 如果需要返回操作，则为 True
    :return: 反馈的情境编号或 None
    """
    self.chat_manager.context_pool["temporary"].refresh()
    self.chat_manager.context_pool["temporary"].copy_from(
      self.chat_manager.context_pool[self.stage]
    )
    user_prompt = user_prompt_analyze_situation(need_back)

    logger.info("Querying Situation")
    response, p_usage, r_usage = self.chat_manager.get_response(
      stage="temporary",
      model="gpt-4-vision-preview",
      prompt=user_prompt,
    )
    logger.info("Situation Feedback Received.")
    logger.info(f"Token Cost: {p_usage} + {r_usage}")
    logger.debug(f"Response: ```{response}```")

    situation = extract_json(response)
    if situation is None \
            or situation.get("situation-number") is None \
            or situation["situation-number"] not in (1, 2, 3, 4):
      logger.error("No Valid Action Found")
      return None
    logger.info(f"Situation Number Extracted: {situation['situation-number']}")
    return situation["situation-number"]
