import os
import json
from typing import Any, Dict, Optional

from agent.logger import logger
from agent.llm import LLMChatManager
from agent.memory import Memory
from agent.utils import gen_timestamp


class TestRecorder:
    """
    TestRecorder 类用于记录操作历史和测试脚本，并根据需要保存完整的聊天上下文。
    """
    def __init__(self, chat_manager: LLMChatManager, base_dir: str):
        """
        初始化 TestRecorder 类，设置基本目录和聊天管理器。
        :param chat_manager: LLMChatManager 实例，用于管理对话
        :param base_dir: 基础目录，用于保存脚本和聊天记录
        """
        # 存储操作历史的列表
        self.history_action = []
        self.chat_manager = chat_manager
        self.script_base_dir = os.path.join(base_dir, "data", "script")
        self.chat_base_dir = os.path.join(base_dir, "data", "chat")

    def record(self, action: Dict[str, Any], memory: Memory, require_widget: bool) -> None:
        """
        记录操作，保存当前截图或包含组件边框的截图。
        :param action: 包含操作信息的字典
        :param memory: Memory 实例，包含应用的当前状态和历史操作
        :param require_widget: 是否需要保存包含组件边框的截图
        """
        # 根据是否需要组件边框，选择当前截图保存到操作记录中
        action["screenshot"] = memory.current_screenshot if not require_widget \
            else memory.current_screenshot_with_bbox
        self.history_action.append(action.copy())

    def scripted(
            self,
            app_id: str,
            scenario_id: str,
            addition: Optional[Dict[str, Any]] = None,
            failed: bool = False,
            full_chat: bool = False,
    ) -> str:
        """
        根据记录的操作生成脚本文件，并可选择保存完整的聊天记录。
        :param app_id: 应用 ID，用于命名文件
        :param scenario_id: 场景 ID，用于命名文件
        :param addition: 额外添加到脚本内容中的信息
        :param failed: 如果测试失败，则在文件名中标记
        :param full_chat: 是否保存完整的聊天上下文
        :return: 生成的脚本文件路径
        """
        timestamp = gen_timestamp()
        # 根据是否失败设置脚本文件名称
        if failed:
            script_file_name = f"{scenario_id}-{app_id}-{timestamp}-failed.json"
        else:
            script_file_name = f"{scenario_id}-{app_id}-{timestamp}.json"
        script_file_path = os.path.join(self.script_base_dir, script_file_name)
        script_content = {"actions": self.history_action}
        if addition is not None:
            script_content.update(addition)
        with open(script_file_path, "w", encoding="utf-8") as f:
            json.dump(script_content, f, indent=2)
        logger.info(f"Script Saved to {script_file_name}")
        if full_chat:
            chat_file_name = f"{scenario_id}-{app_id}-{timestamp}-chat.txt"
            chat_file_path = os.path.join(self.chat_base_dir, chat_file_name)
            self.chat_manager.refresh_context()
            chat_file_content = self.chat_manager.context_pool2string()
            with open(chat_file_path, "w", encoding="utf-8") as f:
                f.write(chat_file_content)
            logger.info(f"Chat Details Saved to {chat_file_name}")
        return script_file_path
