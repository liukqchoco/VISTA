from typing import Any, Dict, Optional
from agent.llm import LLMChatManager
from agent.logger import logger
from agent.memory import Memory
from agent.prompt.decider import system_prompt_next_action, user_prompt_next_action, user_prompt_modify_next_action
from agent.utils import extract_json

class Perceiver:
    def __init__(self, chat_manager: LLMChatManager):
        self.chat_manager = chat_manager
        self.stage = "action-decision"

    def understanding(
            self,
            memory: Memory,
            correcting: bool = False,
            situation: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        if not correcting:
            sys_prompt = system_prompt_next_action(memory=memory)
            user_prompt = user_prompt_next_action(memory=memory)
            user_message = {"text": user_prompt, "image": memory.current_screenshot}
            self.chat_manager.context_pool[self.stage].refresh()
            logger.info("Understanding Scenario") ##Before:Deciding Next Action
        else:
            assert situation is not None
            sys_prompt = None
            user_message = user_prompt_modify_next_action(situation)
            logger.info("Re-Understanding Scenario")##Re-Deciding Next Action

        response, p_usage, r_usage = self.chat_manager.get_response(
            stage=self.stage,
            model="gpt-4-vision-preview",
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
