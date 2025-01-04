import os

os.environ["HTTP_PROXY"] = "http://127.0.0.1:10809"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:10809"

import base64
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI

client = OpenAI(
    base_url="https://api.openai.com/v1",
    api_key="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"
)

def encode_image(image_path: str):
    """
    对指定路径的图像进行 base64 编码。
    :param image_path: 图像文件的路径
    :return: 编码后的 base64 字符串
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def build_content(
        message: Union[str, Dict[str, Any]],
) -> Union[str, List[Dict[str, Any]]]:
    """
    构建用户消息内容，根据输入类型生成不同的格式。
    :param message: 可以是字符串类型的文本，或包含图像路径和文本的字典
    :return: 字符串类型的文本或包含文本和图像的内容列表
    :raises TypeError: 如果输入的 message 格式不正确
    """
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        image = message.get("image")
        text = message.get("text")
        if image is None or text is None:
            raise TypeError(message)
        if isinstance(image, str):
            image = [image]

        user_content = [{"type": "text", "text": text}]
        for image_path in image:
            base64_image = encode_image(image_path)
            # 将编码后的图像添加到用户内容列表中
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
            })
        return user_content

    # 如果 message 既不是字符串也不是字典，抛出类型错误
    raise TypeError(message)


def build_messages(
        user_messages: List[Union[str, Dict[str, Any]]],
        system_message: Optional[str] = None,
        assistant_messages: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    构建对话消息，组织系统消息、用户消息和助手消息的结构。
    :param user_messages: 用户消息的列表，可以是字符串或包含图像的字典
    :param system_message: 可选的系统消息，作为对话背景设置
    :param assistant_messages: 可选的助手消息列表，是GPT对用户消息的回复
    :return: 组织好的消息列表
    :raises RuntimeError: 如果用户消息和助手消息的数量不匹配
    """
    messages = []
    # 添加系统消息
    if system_message is not None:
        messages.append({"role": "system", "content": system_message})
    # 添加用户消息
    if assistant_messages is None and len(user_messages) == 1:
        user_content = build_content(user_messages[0])
        messages.append({"role": "user", "content": user_content})
    # 如果assistant_messages不是空，那么有对话历史。将用户消息与助手的回复消息进行配对，以构建一个完整的对话历史
    elif assistant_messages is not None and len(user_messages) == len(assistant_messages) + 1:
        for i in range(len(assistant_messages)):
            user_content = build_content(user_messages[i])
            messages.append({"role": "user", "content": user_content})
            messages.append({"role": "assistant", "content": assistant_messages[i]})
        user_content = build_content(user_messages[-1])
        messages.append({"role": "user", "content": user_content})
    else:
        raise RuntimeError("Message Numbers Mismatched")
    return messages


class ChatContext:
    # 用于管理对话上下文
    def __init__(
            self,
            user_messages: Optional[List[Union[str, Dict[str, Any]]]] = None,
            assistant_messages: Optional[List[str]] = None,
            system_message: Optional[str] = None,
    ):
        """
        初始化 ChatContext 类，设置对话的初始上下文信息。
        :param user_messages: 用户消息的列表，可以为空
        :param assistant_messages: 助手消息的列表，即GPT生成对话的历史记录可以为空
        :param system_message: 系统消息，用于设置对话背景，可以为空
        """
        self.user_messages = user_messages
        self.assistant_messages = assistant_messages
        self.system_message = system_message
        self.history_storage = []  # 用于存储历史对话

    def append_user_message(self, message: Union[str, Dict[str, Any]]) -> None:
        """
        向用户消息列表添加新的消息。
        :param message: 用户消息，可以是字符串或包含图像的字典
        """
        if self.user_messages is None:
            self.user_messages = []
        self.user_messages.append(message)

    def append_assistant_message(self, message: str) -> None:
        """
        向助手消息列表添加新的消息。
        :param message: 助手的回复消息，字符串类型
        """
        if self.assistant_messages is None:
            self.assistant_messages = []
        self.assistant_messages.append(message)

    def set_system_message(self, message: str) -> None:
        """
        设置系统消息，如果系统消息未设置过则赋值。
        :param message: 系统消息内容
        """
        if self.system_message is None:
            self.system_message = message

    def copy_from(self, other: "ChatContext") -> None:
        """
        从另一个 ChatContext 对象复制消息内容到当前对象。
        :param other: 另一个 ChatContext 实例
        """
        self.user_messages = other.user_messages
        self.assistant_messages = other.assistant_messages
        self.system_message = other.system_message

    def messages(self) -> List[Dict[str, Any]]:
        """
        构建并返回当前对话的完整消息列表。
        :return: 组织好的对话消息列表
        :raises RuntimeError: 如果没有用户消息，则抛出运行时错误
        """
        if self.user_messages is not None:
            return build_messages(
                user_messages=self.user_messages,
                system_message=self.system_message,
                assistant_messages=self.assistant_messages,
            )
        raise RuntimeError("No User Message Found")

    def refresh(self) -> None:
        """
        刷新对话上下文，将当前对话内容存储到历史记录中，并重置当前对话。
        """
        # 有历史对话记录
        if self.user_messages is not None and self.assistant_messages is not None:
            assert len(self.user_messages) == len(self.assistant_messages)
            # 将当前对话存入历史存储中
            self.history_storage.append((
                self.system_message,
                self.user_messages,
                self.assistant_messages
            ))
        # 重置各类消息（相当于重新开了一个GPT窗口，清空历史记录）
        self.system_message = None
        self.user_messages = None
        self.assistant_messages = None

    def __str__(self):
        """
       将历史对话上下文转换为字符串格式。
       :return: 包含历史对话的字符串
       """
        context_str = ""
        for i, context in enumerate(self.history_storage):
            # 添加上下文编号
            context_str += f"CONTEXT-{i}:\n"
            system, user, assistant = context
            # 添加系统消息
            if system is not None:
                context_str += f"- SYS: ```{system}```\n"
            for j in range(len(user)):
                # 添加用户图像和文本消息
                if isinstance(user[j], dict):
                    txt_prompt = user[j]["text"]
                    img_prompt = user[j]["image"]
                    context_str += f"- USER: ```{img_prompt}\n{txt_prompt}```\n"
                # 添加用户文本消息
                else:
                    context_str += f"- USER: ```{user[j]}```\n"
                # 添加助手消息
                context_str += f"- ASSI: ```{assistant[j]}```\n"
            context_str += "\n"
        return context_str.strip()


class LLMChatManager:
    """
    LLMChatManager 类用于管理多个对话上下文，并处理基于大语言模型 (LLM) 的对话请求。
    """
    def __init__(self):
        """
        初始化 LLMChatManager 类，创建不同类型的对话上下文，并将其存储到 context_pool 中。
        """
        self.action_decision_context = ChatContext()
        self.loading_check_context = ChatContext()
        self.ending_check_context = ChatContext()
        self.visual_change_check_context = ChatContext()
        self.valid_change_check_context = ChatContext()
        self.temporary_context = ChatContext()
        # 创建一个上下文池，将各个上下文对象存储在字典中，方便管理和访问
        self.context_pool: Dict[str, ChatContext] = {
            "action-decision": self.action_decision_context,
            "loading-check": self.loading_check_context,
            "ending-check": self.ending_check_context,
            "visual-change-check": self.visual_change_check_context,
            "valid-change-check": self.valid_change_check_context,
            "temporary": self.temporary_context,
        }

    def refresh_context(self) -> None:
        """
        刷新所有上下文，将当前对话内容存储到历史记录中，并重置每个上下文。
        """
        for context in self.context_pool.values():
            context.refresh()

    def context_pool2string(self) -> str:
        """
        将上下文池中的所有上下文转换为字符串，方便查看每个阶段的对话内容。
        :return: 包含所有上下文内容的字符串
        """
        context_pool_str = ""
        for stage, context in self.context_pool.items():
            context_pool_str += f"**STAGE {stage}**\n"
            context_pool_str += f"{str(context)}\n\n\n"
        return context_pool_str.strip()

    def get_response(
            self,
            stage: str,
            model: str,
            prompt: Union[str, Dict[str, Any]],
            system: Optional[str] = None,
            max_tokens: int = 1024,
            temperature: float = 0.0,
    ):
        """
        获取对话模型的回复，并更新对应的上下文。
        :param stage: 上下文阶段的名称，对应 context_pool 中的键值
        :param model: 使用的大语言模型的名称
        :param prompt: 用户输入的提示，可以是字符串或包含更多信息的字典
        :param system: 可选的系统消息，用于设置对话的背景
        :param max_tokens: 最大生成的 token 数量，控制回复的长度
        :param temperature: 控制生成文本的随机性，值越高表示生成越随机
        :return: 包含回复内容、提示词消耗的 token 数量和回复消耗的 token 数量的元组
        """
        target_context = self.context_pool[stage]
        target_context.append_user_message(prompt)
        if system is not None:
            target_context.set_system_message(system)
        messages = target_context.messages()
        # 使用 OpenAI 客户端请求对话模型生成回复
        response = client.chat.completions.create(
            model="gpt-4o",
            # model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 从生成的响应中获取 token 消耗信息
        prompt_cost = response.usage.prompt_tokens
        response_cost = response.usage.completion_tokens
        # 提取模型生成的回复内容
        response_content = response.choices[0].message.content
        # 将回复添加到助手上下文中
        target_context.append_assistant_message(response_content)
        return response_content, prompt_cost, response_cost
