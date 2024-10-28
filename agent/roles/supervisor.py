from typing import Tuple, Optional

from agent.llm import LLMChatManager
from agent.logger import logger
from agent.memory import Memory
from agent.prompt.supervisor import (
    system_prompt_effect_check,
    system_prompt_ending_check,
    system_prompt_loading_check,
    user_prompt_ending_check,
    user_prompt_loading_check,
    user_prompt_page_change_check,
    user_prompt_valid_change_check,
)


class TestSupervisor:
    """
    TestSupervisor 类用于监控测试流程，通过 LLM 对不同场景下的页面加载、结束和效果变化进行检查。
    """
    def __init__(self, chat_manager: LLMChatManager):
        """
        初始化 TestSupervisor 实例，设置检查阶段和聊天管理器。
        :param chat_manager: LLMChatManager 实例，用于处理不同阶段的对话上下文
        """
        self.chat_manager = chat_manager
        self.stage_load = "loading-check"
        self.stage_end = "ending-check"
        self.stage_visual_change = "visual-change-check"
        self.stage_valid_change = "valid-change-check"

    def check_loading(self, memory: Memory) -> Optional[bool]:
        """
        检查当前页面是否处于加载状态。
        :param memory: Memory 实例，用于提供必要的上下文信息
        :return: 如果加载中返回 True, 否则返回 False; 格式错误则返回 None
        """
        sys_prompt = system_prompt_loading_check()
        user_prompt = user_prompt_loading_check()
        user_message = {"text": user_prompt, "image": memory.cached_screenshot}
        self.chat_manager.context_pool[self.stage_load].refresh()

        logger.info("Start Loading Check")
        response, p_usage, r_usage = self.chat_manager.get_response(
            stage=self.stage_load,
            model="gpt-4-vision-preview",
            prompt=user_message,
            system=sys_prompt,
        )
        logger.info("Check Result Received")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        index = response.find("answer:")
        if index == -1:
            if response.startswith("T"):
                logger.warning("Non-standardized Response Format")
                return True
            if response.startswith("F"):
                logger.warning("Non-standardized Response Format")
                return False
            logger.error("Invalid Response Format")
            return None
        response = response[index:]
        if response[8] == "T":  # answer: T/F\n
            return True
        elif response[8] == "F":
            return False
        else:
            logger.error("Invalid Response Format")
            return None

    def check_end(self, memory: Memory) -> Optional[bool]:
        """
        检查当前操作是否已结束。
        :param memory: Memory 实例，用于提供必要的上下文信息
        :return: 如果结束返回 True, 否则返回 False; 格式错误则返回 None
        """
        sys_prompt = system_prompt_ending_check(memory)
        task_prompt, prev_screen_prompt, curr_screen_prompt, init_screen_prompt \
            = user_prompt_ending_check(memory)
        prev_screen_message = {"text": prev_screen_prompt, "image": memory.current_screenshot}
        curr_screen_message = {"text": curr_screen_prompt, "image": memory.cached_screenshot}
        init_screen_message = {"text": init_screen_prompt, "image": memory.initial_screenshot}

        self.chat_manager.context_pool[self.stage_end].refresh()
        self.chat_manager.context_pool[self.stage_end].set_system_message(sys_prompt)
        self.chat_manager.context_pool[self.stage_end].append_user_message(init_screen_message)
        self.chat_manager.context_pool[self.stage_end].append_assistant_message("")
        self.chat_manager.context_pool[self.stage_end].append_user_message(prev_screen_message)
        self.chat_manager.context_pool[self.stage_end].append_assistant_message("")
        self.chat_manager.context_pool[self.stage_end].append_user_message(curr_screen_message)
        self.chat_manager.context_pool[self.stage_end].append_assistant_message("")

        logger.info("Start Ending Check")
        response, p_usage, r_usage = self.chat_manager.get_response(
            stage=self.stage_end,
            model="gpt-4-vision-preview",
            prompt=task_prompt,
        )
        logger.info("Check Result Received")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        index = response.find("answer:")
        if index == -1:
            if response.startswith("T"):
                logger.warning("Non-standardized Response Format")
                return True
            if response.startswith("F"):
                logger.warning("Non-standardized Response Format")
                return False
            logger.error("Invalid Response Format")
            return None
        response = response[index:]
        if response[8] == "T":  # answer: T/F\n
            return True
        elif response[8] == "F":
            return False
        else:
            logger.error("Invalid Response Format")
            return None

    def check_effect(self, memory: Memory) -> Tuple[Optional[bool], Optional[bool]]:
        """
        检查页面是否有预期的效果变化，返回页面变化和有效变化的状态。
        :param memory: Memory 实例，用于提供必要的上下文信息
        :return: (是否有效变化, 是否页面变化)
        """
        valid_change = self._check_valid_page_change(memory)
        if valid_change is None:
            return None, None
        if valid_change:
            return True, False
        page_change = self._check_page_change(memory)
        if page_change is None:
            return None, None
        if page_change:
            return False, True
        return False, False

    def _check_page_change(self, memory: Memory) -> Optional[bool]:
        """
        检查页面是否发生了变化。
        :param memory: Memory 实例，用于提供必要的上下文信息
        :return: 如果页面变化返回 True, 否则返回 False; 格式错误则返回 None
        """
        sys_prompt = system_prompt_effect_check()
        task_prompt, prev_screen_prompt, curr_screen_prompt = user_prompt_page_change_check()
        prev_screen_message = {"text": prev_screen_prompt, "image": memory.current_screenshot}
        curr_screen_message = {"text": curr_screen_prompt, "image": memory.cached_screenshot}

        self.chat_manager.context_pool[self.stage_visual_change].refresh()
        self.chat_manager.context_pool[self.stage_visual_change].set_system_message(sys_prompt)
        self.chat_manager.context_pool[self.stage_visual_change].append_user_message(task_prompt)
        self.chat_manager.context_pool[self.stage_visual_change].append_assistant_message("")
        self.chat_manager.context_pool[self.stage_visual_change].append_user_message(prev_screen_message)
        self.chat_manager.context_pool[self.stage_visual_change].append_assistant_message("")

        logger.info("Checking Page Change")
        response, p_usage, r_usage = self.chat_manager.get_response(
            stage=self.stage_visual_change,
            model="gpt-4-vision-preview",
            prompt=curr_screen_message,
        )
        logger.info("Check Result Received")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        index = response.find("answer:")
        if index == -1:
            if response.find("YES") != -1:
                logger.warning("Non-standardized Response Format")
                return True
            if response.find("NO") != -1:
                logger.warning("Non-standardized Response Format")
                return False
            logger.error("Invalid Response Format")
            return None
        response = response[index:]
        if response.startswith("answer: YES"):
            return True
        elif response.startswith("answer: NO"):
            return False
        else:
            logger.error("Invalid Response Format")
            return None

    def _check_valid_page_change(self, memory: Memory) -> Optional[bool]:
        """
        检查页面是否发生了符合场景的有效变化。
        :param memory: Memory 实例，用于提供必要的上下文信息
        :return: 如果有效变化返回 True, 否则返回 False; 格式错误则返回 None
        """
        sys_prompt = system_prompt_effect_check()
        task_prompt, prev_screen_prompt, curr_screen_prompt, init_screen_prompt \
            = user_prompt_valid_change_check(memory)
        prev_screen_message = {"text": prev_screen_prompt, "image": memory.current_screenshot}
        curr_screen_message = {"text": curr_screen_prompt, "image": memory.cached_screenshot}
        init_screen_message = {"text": init_screen_prompt, "image": memory.initial_screenshot}

        self.chat_manager.context_pool[self.stage_valid_change].refresh()
        self.chat_manager.context_pool[self.stage_valid_change].set_system_message(sys_prompt)
        self.chat_manager.context_pool[self.stage_valid_change].append_user_message(task_prompt)
        self.chat_manager.context_pool[self.stage_valid_change].append_assistant_message("")
        self.chat_manager.context_pool[self.stage_valid_change].append_user_message(init_screen_message)
        self.chat_manager.context_pool[self.stage_valid_change].append_assistant_message("")
        self.chat_manager.context_pool[self.stage_valid_change].append_user_message(prev_screen_message)
        self.chat_manager.context_pool[self.stage_valid_change].append_assistant_message("")

        logger.info("Checking Valid Page Change")
        response, p_usage, r_usage = self.chat_manager.get_response(
            stage=self.stage_valid_change,
            model="gpt-4-vision-preview",
            prompt=curr_screen_message,
        )
        logger.info("Check Result Received")
        logger.info(f"Token Cost: {p_usage} + {r_usage}")
        logger.debug(f"Response: ```{response}```")

        index = response.find("answer:")
        if index == -1:
            if response.find("YES") != -1:
                logger.warning("Non-standardized Response Format")
                return True
            if response.find("NO") != -1:
                logger.warning("Non-standardized Response Format")
                return False
            logger.error("Invalid Response Format")
            return None
        response = response[index:]
        if response.startswith("answer: YES"):
            return True
        elif response.startswith("answer: NO"):
            return False
        else:
            logger.error("Invalid Response Format")
            return None
