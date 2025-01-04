import json
import time
from typing import Any, Dict, List, Optional


def gen_timestamp() -> str:
  """
  生成当前的时间戳字符串。
  :return: 当前时间戳的字符串形式
  """
  timestamp = int(time.time())
  return str(timestamp)


def extract_json(s: str) -> Optional[Dict[str, Any]]:
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
      if stack:
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


def remove_punctuation(s: str, more_punc: Optional[List[str]] = None) -> str:
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
