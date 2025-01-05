# 软件测试2024大作业——**大模型引导的场景感知** **GUI** 探索测试选题说明文档

# 补充说明

为了保证项目高效开发，我们采取了前后端分离的方式

1. 后端：实现GUI自动化测试的核心代码，即为该仓库
2. 前端：Web界面的实现代码请见https://github.com/Xuzhanghan/VISTA_Web/tree/master

# 文档结构

该项目文档由以下两部分组成：

1. 功能模块及交互说明：详细描述该项目的功能模块及交互
2. 项目运行说明：详细讲述运行要求，可根据文档运行工具

# 一、功能模块及交互说明

## 项目概述

本项目设计了一种基于大模型 (大语言与多模态大语言模型) 引导的场景感知 GUI 自动化探索测试技术，旨在提升测试覆盖率与可靠性，解决传统探索测试无法深刻理解业务逻辑的问题。通过结合大语言模型的场景理解能力和自动化测试工具的执行能力，项目实现了从场景感知到结果验证的完整测试工作流。

系统功能模块包括：
1. 测试场景的感知与理解
2. 基于场景的测试操作生成与执行
3. 基于场景的应用状态验证
4. 完整的自动化 GUI 测试探索工作流
5. 交互界面设计与实现

## 功能模块及交互逻辑

### 1. 测试场景感知与理解

#### 功能描述
系统通过用户输入和大语言模型的分析能力，解析测试目标，并实时感知应用状态，为后续操作生成与验证提供依据。

#### 1.1 场景目标感知

- **关键方法**：
  - `TestAgent.initialize`：接收用户输入的场景描述，初始化测试任务。
  - 内部调用 `Memory.add_basic_info` 将场景信息存储，包括应用名称、包名、目标场景描述、额外场景信息等。
  - 使用 `DeviceManager.launch_app` 启动目标应用，为测试准备运行环境。

- **交互逻辑**：
  1. 用户通过前端界面提供测试目标场景（如应用名称、包名、启动活动、场景目标描述）。
  2. 后端调用 `TestAgent.initialize`，存储目标信息，并启动应用。
  3. 应用启动完成后，系统记录其初始状态，进入测试准备状态。

#### 1.2 应用状态实时分析

- **关键方法**：
  - `Perceiver.understanding`：结合应用截图和场景描述，通过 LLM 生成当前状态的语义理解。
  - LLM 返回应用界面状态与目标场景的关联信息。

- **交互逻辑**：
  1. 系统截取当前应用界面，将截图与场景上下文通过 `Perceiver` 提交至 LLM。
  2. LLM 分析返回状态描述，指出与目标的偏差。
  3. 分析结果存储至内存模块，供操作生成模块使用。

### 2. 基于场景的测试操作生成与执行

#### 功能描述
根据场景目标和当前状态，系统生成符合逻辑的测试操作，并通过自动化工具执行这些操作。

#### 2.1 测试操作生成

- **关键方法**：
  - `ActionDecider.next_action`：从内存中提取目标场景与当前状态，通过 LLM 决策下一步操作。
  - 生成的操作包括点击、输入文本、滑动页面等。

- **交互逻辑**：
  1. 系统从内存模块提取当前状态和目标场景信息。
  2. `ActionDecider` 调用 LLM 分析最佳操作，并返回操作指令（如目标组件位置、操作类型）。
  3. 操作信息传递至执行模块。

#### 2.2 测试操作执行

- **关键方法**：
  - `ActionExecutor.execute`：接收操作指令并通过 ADB 指令执行具体操作。

- **交互逻辑**：
  1. 接收操作生成模块的指令。
  2. 使用设备管理工具将指令转化为具体的 ADB 命令并执行。
  3. 返回执行结果至状态验证模块。

### 3. 应用状态验证与修正

#### 功能描述
验证操作是否成功，应用状态是否达到目标；若未成功，则生成修正操作。

#### 3.1 应用状态验证

- **关键方法**：
  - `TestSupervisor.check_effect`：通过比较当前状态与目标状态，判断操作是否成功。

- **交互逻辑**：
  1. 从内存模块提取目标状态和当前状态。
  2. 调用 LLM 验证状态是否与目标一致。
  3. 若验证失败，将偏差信息存储，用于修正模块生成替代操作。

#### 3.2 状态修正

- **关键方法**：
  - `TestAgent._state_correcting`：分析偏差原因，通过 LLM 生成修正操作。

- **交互逻辑**：
  1. 验证发现偏差后，系统进入状态修正逻辑。
  2. 调用 LLM 分析当前状态与目标状态的差异，生成新的操作建议。
  3. 新的操作指令传递至执行模块，并重复验证流程。

### 4. 自动化测试工作流

#### 功能描述
通过模块间的协调，构建完整的自动化测试探索工作流，包括任务初始化、循环操作、状态修正与结束。

#### 实现逻辑

1. **任务初始化**：
   - 用户通过界面输入测试场景目标。
   - 系统调用 `TestAgent.initialize` 方法设置任务目标并启动应用。

2. **循环流程**：
   - **场景感知**：系统调用 `Perceiver` 提取当前状态信息。
   - **操作生成**：调用 `ActionDecider` 根据目标和当前状态生成测试操作。
   - **操作执行**：通过 `ActionExecutor` 将操作发送至设备。
   - **状态验证**：调用 `TestSupervisor` 检查操作效果。
   - **状态修正**：若状态不符合预期，调用修正逻辑生成新操作。

3. **任务结束**：
   - 当验证模块确认目标状态达到，或无进一步操作时，系统结束测试。
   - 生成最终的测试报告。

### 5. 交互界面设计

#### 功能描述
提供基于 Web 的用户界面，支持任务配置、启动、终止，以及测试结果的可视化展示。

后端采用**Flask框架**进行设计，提供对应测试接口

#### 实现逻辑
1. **任务初始化**：
   - 用户在界面输入测试目标，前端通过 API 将数据发送至后端。
   - 后端调用 `TestAgent.initialize` 设置任务。

2. **任务执行**：
   - 用户发起单步执行请求，后端调用测试工作流模块完成一步操作并返回当前状态。
   - 前端实时展示测试进度。

3. **结果展示**：
   - 测试结束后，前端接收后端生成的测试报告，并展示任务成功率、操作日志、失败原因等信息。



# 二、项目运行说明

## 系统运行要求

### 硬件环境

- 操作系统：Windows/Linux/macOS
- 设备：支持 ADB 的 Android 设备

### 软件环境

- Python3（>=3.8,<=3.10）
- Android SDK（主要使用 ADB 工具）

### 后端初始化

以下配置项均在 `config/application.yml` 中配置。

1. 测试相关（`test`）：
   1. `host`：后端服务的 IP 地址
   2. `port`：后端服务的端口号
   3. `adb_path`：ADB 工具的路径
   4. `root_input`：UIED 工具的输入根目录
   5. `root_output`：UIED 工具的输出根目录
   6. `ocr_model_path`：OCR 模型的路径，运行时会自动下载
   7. `app_id`：对应 `conf.json` 中应用的 ID，仅用于后端独立测试
   8. `scenario_id`：对应 `conf.json` 中场景的 ID，仅用于后端独立测试

2. 设备相关（`device`）：
   1. `screenshot_path`：截图在待测设备上的存储路径
   2. `gui_xml_path`：UIED 工具生成的 XML 文件在待测设备上的存储路径

3. 大模型相关（`llm`）：
   1. `http_proxy`：HTTP 代理地址，用以访问 OpenAI API
   2. `https_proxy`：HTTPS 代理地址，作用同上
   3. `base_url`：大模型的 API 地址
   2. `api_key`：API 的密钥

4. 特别注意：项目路径**禁止**包含中文，cv2包无法读取中文路径下的图片

### 项目运行

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 启动Flask后端服务：

   ```bash
   python app.py
   ```

3. 调用 API 或使用前端Web界面完成测试探索。
