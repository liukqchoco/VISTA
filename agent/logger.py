import logging

# 配置日志系统的基础设置（默认设置）
logging.basicConfig()
# 获取名为 "agent" 的 logger 对象
logger = logging.getLogger("agent")


def init_logger(_logger, filepath, mode="a"):
    """
    初始化 logger 对象，设置日志输出格式、控制台和文件输出方式。
    :param _logger: 要初始化的 logger 实例
    :param filepath: 日志文件的保存路径
    :param mode: 文件打开模式，默认为追加模式 "a"
    """

    # 设置 logger 的日志级别为 DEBUG，记录所有级别的日志
    _logger.setLevel(logging.DEBUG)

    # 定义日志输出的格式，包括时间、日志级别、logger 名称、模块名、日志消息
    fmt = '%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s'
    # 创建日志格式化器
    formatter = logging.Formatter(fmt)

    # 创建控制台日志处理器
    console = logging.StreamHandler()  # 将日志输出到控制台
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)  # 设置控制台日志输出格式
    _logger.addHandler(console)  # 将控制台处理器添加到 logger 中

    # 创建文件日志处理器
    fout = logging.FileHandler(filepath, mode=mode)  # 将日志输出到指定文件
    fout.setLevel(logging.DEBUG)
    fout.setFormatter(formatter)
    _logger.addHandler(fout)

    # 禁止日志向上层 logger 传递，避免重复输出
    _logger.propagate = False

    _logger.info('logger inited')

# 初始化 logger，将日志保存到 "agent.log" 文件中，文件模式为写入模式 "w"
init_logger(logger, "agent.log", "w")
