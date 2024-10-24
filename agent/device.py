import os
import platform
import subprocess
import time
from typing import Optional, Tuple

import cv2

from agent.logger import logger
from agent.utils import gen_timestamp


class Device:
    """
    表示一个设备类，初始化设备并获取设备信息。
    """
    def __init__(self, device_platform: str = "android", device_id: Optional[str] = None):
        """
        初始化设备类，支持 Android 平台，并通过 adb 获取连接设备信息。
        :param device_platform: 设备平台（默认为 Android）
        :param device_id: 设备 ID（可选，默认为 None）
        """
        self.platform = device_platform
        if self.platform == "android":
            # 使用 adb 命令列出连接的设备
            # subprocess.run()可以执行外部命令，"adb devices"其实就是一种参数
            output = subprocess.run("adb devices", shell=True, capture_output=True, text=True)
            # 获取设备 ID 列表
            device_list = [line.split("\t")[0] for line in output.stdout.strip().split("\n")[1:]]
            if len(device_list) == 0:
                raise RuntimeError("No devices available")
            else:
                if device_id is None:
                    # 如果未指定设备 ID，选择第一个设备
                    self.device_id = device_list[0]
                elif device_id in device_list:
                    # 如果设备 ID 存在于设备列表中，设置为该设备
                    self.device_id = device_id
                else:
                    raise ValueError(f"Unknown device_id: {device_id}")
            self.width = None
            self.height = None
        else:
            raise ValueError(f"Unsupported platform: {platform}")
        
        
class DeviceManager:
    """
    设备管理类，用于管理和操作 Android 设备。包括点击、输入文本、滑动、安装卸载应用等功能。
    """
    def __init__(self, device: Device, base_dir: str, mode: str = "SILENT"):
        """
        初始化设备管理器。
        :param device: 设备实例，表示当前连接的 Android 设备。
        :param base_dir: 基础目录，用于存储相关的截图、XML 和 APK 文件。
        :param mode: 模式，默认是 "SILENT"，可选 "DEBUG" 模式用于调试。
        """
        self.mode = mode
        self.device = device
        self.resize_ratio = None
        # 获取当前运行的应用包名
        self.default_package = self.get_current_app_message()[0]
        self.special_character = ("'", "?", "&", "#", "<", ">")
        self.xml_folder = os.path.join(base_dir, "data", "xml")
        self.apk_folder = os.path.join(base_dir, "data", "apk")
        self.screenshot_folder = os.path.join(base_dir, "data", "input")
        self.marked_screenshot_folder = os.path.join(base_dir, "output", "merge")

    def set_resize_ratio(self, ratio: float) -> None:
        """
        设置截图或点击的缩放比例。
        :param ratio: 缩放比例，float 类型。
        """
        self.resize_ratio = ratio
        if self.mode == "DEBUG":
            logger.debug(f"Resize Ratio Set: {self.resize_ratio}")

    def op_click(self, x: int, y: int) -> str:
        """
        模拟点击指定的坐标位置。
        :param x: X 坐标
        :param y: Y 坐标
        :return: 返回执行的 ADB 命令字符串
        """
        if self.resize_ratio is not None:
            x = x // self.resize_ratio
            y = y // self.resize_ratio
        else:
            logger.warning("Resize ratio not set")
        cmd = f"adb -s {self.device.device_id} shell input tap {x} {y}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: click on x={x}, y={y}")
        return cmd

    def op_input(self, text: str) -> str:
        """
        模拟输入指定的文本。
        :param text: 要输入的文本内容
        :return: 返回执行的 ADB 命令字符串
        """
        text_bk = text
        if len(text) > 0:
            # 处理特殊字符和空格符号，使其可以正确通过 ADB 输入
            text = text.replace(" ", "%s")
            text = text.replace('"', "'")
            for char in self.special_character:
                text = text.replace(f"{char}", f"\\{char}")
            cmd = f"adb -s {self.device.device_id} shell input text \"{text}\""
            subprocess.run(cmd, shell=True)
        else:
            cmd = "input blank string"
        if self.mode == "DEBUG":
            text = text_bk.replace("\n", "\\n")
            logger.debug(f"Execution: input text ```{text}```")
        return cmd

    def op_scroll(self, x_start: int, y_start: int, x_end: int, y_end: int, duration: int = 500) -> str:
        """
        模拟滑动屏幕操作。
        :param x_start: 起始 X 坐标
        :param y_start: 起始 Y 坐标
        :param x_end: 结束 X 坐标
        :param y_end: 结束 Y 坐标
        :param duration: 滑动持续时间，默认为 500 毫秒
        :return: 返回执行的 ADB 命令字符串
        """
        cmd = f"adb -s {self.device.device_id} shell input swipe {x_start} {y_start} {x_end} {y_end} {duration}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: swipe screen ({x_start}, {y_start}) to ({x_end}, {y_end})")
        return cmd
    
    def install_app(self, apk_path: str) -> str:
        """
        安装 APK 应用。
        :param apk_path: APK 文件路径
        :return: 返回执行的 ADB 命令字符串
        """
        cmd = f"adb -s {self.device.device_id} install {apk_path}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Installed: {apk_path}")
        return cmd

    def uninstall_app(self, app_package: str) -> str:
        """
        卸载应用程序。
        :param app_package: 应用包名
        :return: 返回执行的 ADB 命令字符串
        """
        cmd = f"adb -s {self.device.device_id} uninstall {app_package}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Uninstalled: {app_package}")
        return cmd

    def get_current_app_message(self) -> Tuple[str, str]:
        """
        获取当前运行应用的包名和活动名。
        :return: 当前应用的包名和活动名（Tuple）
        """
        system_name = platform.system().lower()
        filter_cmd = "findstr" if system_name == "windows" else "grep"
        #cmd = f"adb -s {self.device.device_id} shell dumpsys window windows | {filter_cmd} mFocusedApp"
        cmd = f"adb -s {self.device.device_id} shell dumpsys window | {filter_cmd} mFocusedApp"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        # 提取应用包名和活动名
        result = result[result.find("u0") + 2:].strip().split(" ")[0]
        package, activity = result.split("/", maxsplit=1)
        return package, activity

    def launch_app(self, app_package: str, app_launch_activity: str) -> str:
        """
        启动指定应用。
        :param app_package: 应用包名
        :param app_launch_activity: 应用启动活动
        :return: 返回执行的 ADB 命令字符串
        """
        cmd = f"adb -s {self.device.device_id} shell am start {app_package}/{app_launch_activity}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Launched: {app_package}/{app_launch_activity}")
        return cmd

    def close_app(self, app_package: str) -> str:
        """
        关闭指定应用。
        :param app_package: 应用包名
        :return: 返回执行的 ADB 命令字符串
        """
        cmd = f"adb -s {self.device.device_id} shell am force-stop {app_package}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"App Stopped: {app_package}")
        return cmd

    def back(self) -> str:
        """
        返回到上一页。
        :return: 返回执行的 ADB 命令字符串
        """
        # 通过 ADB 模拟返回键按键操作
        cmd = f"adb -s {self.device.device_id} shell input keyevent 4"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: back")
        return cmd

    def wait(self) -> str:
        """
        等待加载完成。
        :return: 返回等待信息
        """
        time.sleep(2)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: wait")
        return "wait 2 seconds"

    def delete_char(self, repeat: int = 1) -> str:
        """
        模拟删除字符操作。
        :param repeat: 重复删除的次数，默认为 1
        :return: 返回执行的 ADB 命令字符串
        """
        cmd = f"adb -s {self.device.device_id} shell input keyevent KEYCODE_DEL"
        for _ in range(repeat):
            subprocess.run(cmd, shell=True)
            time.sleep(.1)
        if self.mode == "DEBUG":
            logger.debug(f"Execution: delete char * {repeat}")
        return f"{cmd} * {repeat}"

    def get_screenshot(self) -> str:
        """
        获取设备截图并保存到本地。
        :return: 返回保存的截图文件路径
        """
        screenshot_src = "/sdcard/screenshot.png"
        screenshot_dest = f"{self.screenshot_folder}/screenshot-{gen_timestamp()}.png"
        # 执行 ADB 命令截取屏幕
        cmd1 = f"adb -s {self.device.device_id} shell screencap -p {screenshot_src}"
        # 将截图文件从设备中拉取到本地
        cmd2 = f"adb pull {screenshot_src} {screenshot_dest}"
        subprocess.run(cmd1, shell=True)
        subprocess.run(cmd2, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"Screenshot Captured: {screenshot_dest}")
        # 如果设备的屏幕宽高未知，则读取截图图像获取宽高
        if self.device.width is None and self.device.height is None:
            screen = cv2.imread(screenshot_dest)
            self.device.width = screen.shape[1]
            self.device.height = screen.shape[0]
        return screenshot_dest

    def get_apk_file(self, app_package: str) -> str:
        """
        从设备中提取应用的 APK 文件。
        :param app_package: 应用包名
        :return: 返回保存的 APK 文件路径
        """
        cmd = f"adb -s {self.device.device_id} shell pm path {app_package}"
        output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        # 从命令输出中提取 APK 文件路径
        apk_file_src = output.stdout.strip("package:")
        apk_file_dest = f"{self.apk_folder}/{gen_timestamp()}.apk"
        # 执行 ADB 命令将 APK 文件拉取到本地
        cmd = f"adb -s {self.device.device_id} pull {apk_file_src} {apk_file_dest}"
        subprocess.run(cmd, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"APK file downloaded: {apk_file_dest}")
        return apk_file_dest

    def dump_gui_xml(self) -> str:
        """
        导出设备界面的 GUI XML 文件。
        :return: 返回保存的 XML 文件路径
        """
        gui_xml_file_src = "/sdcard/ui-dump.xml"
        gui_xml_file_dest = f"{self.xml_folder}/ui-dump-{gen_timestamp()}.xml"
        cmd1 = f"adb -s {self.device.device_id} shell /system/bin/uiautomator dump --compressed {gui_xml_file_src}"
        # 将生成的 XML 文件拉取到本地
        cmd2 = f"adb pull {gui_xml_file_src} {gui_xml_file_dest}"
        subprocess.run(cmd1, shell=True)
        subprocess.run(cmd2, shell=True)
        if self.mode == "DEBUG":
            logger.debug(f"GUI XML Dumped: {gui_xml_file_dest}")
        return gui_xml_file_dest
