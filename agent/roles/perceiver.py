from typing import Any, Dict, Optional

from agent.llm import LLMChatManager
from agent.logger import logger
from agent.memory import Memory
from agent.prompt.decider import system_prompt_next_action, user_prompt_next_action, user_prompt_modify_next_action
from agent.utils import extract_json


class Perceiver:
  """
  Perceiver 类用于理解当前场景，包括用户的操作和系统的反馈，以便做出下一步的决策。
  """

  def __init__(self, chat_manager: LLMChatManager):
    """
    初始化 Perceiver 类，设置聊天管理器。
    :param chat_manager: LLMChatManager 实例，用于管理对话上下文
    """
    self.chat_manager = chat_manager
    self.stage = "action-decision"

  def understanding(
          self,
          memory: Memory,
          correcting: bool = False,
          situation: Optional[str] = None,
  ) -> Optional[Dict[str, Any]]:
    """
    理解当前场景，包括用户的操作和系统的反馈，以便做出下一步的决策。
    :param memory: Memory 实例，用于存储和管理对话历史和上下文
    :param correcting: 是否为修正模式，用于重新理解上下文
    :param situation: 需要修正的情境，用于重新理解上下文
    :return: 理解的场景信息，包括意图和动作类型等
    """
    if not correcting:
      sys_prompt = system_prompt_next_action(memory=memory)
      user_prompt = user_prompt_next_action(memory=memory)
      user_message = {"text": user_prompt, "image": memory.current_screenshot}
      self.chat_manager.context_pool[self.stage].refresh()
      logger.info("Understanding Scenario")  ##Before:Deciding Next Action
    else:
      assert situation is not None
      sys_prompt = None
      user_message = user_prompt_modify_next_action(situation)
      logger.info("Re-Understanding Scenario")  ##Re-Deciding Next Action

    response, p_usage, r_usage = self.chat_manager.get_response(
      stage=self.stage,
      model="gpt-4o",
      prompt=user_message,
      system=sys_prompt,
    )
    logger.info("Scenario Understanding Received.")
    logger.info(f"Token Cost: {p_usage} + {r_usage}")
    logger.debug(f"Response: ```{response}```")

    action = extract_json(response)
    if action is None or action.get("intent") is None or action.get("action-type") is None:
      logger.error("Understanding Failed.")
      return None

    logger.info("Scenario perceived.")
    return action
