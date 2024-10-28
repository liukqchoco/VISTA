# VISTA: Vision-Integrated Scenario-aware GUI Testing with VLM Agents
- 借助GPT大概写了一个说明文档，但是GPTemm错的太多了，我也没办法把整个项目输进去，只是大量的手写prompt+一些关键代码，导致GPT的结果较差
- 在修改之后，我大概总结为了以下两个部分，供大家参考理解
- 其中我之前主要负责的是LLM agent的交互部分，包括supervisor, decider（就是roles文件夹底下的那些）等等，但是observer不是我写的，是基于UIED库魔改的，这里我也不太懂emm，可以大家一起看看
- 然后肯定要在此基础上进行修改，大家可以先想想，之后咱们详细讨论
## 项目框架
### 基于大模型的场景化GUI测试项目教学文档

本文档将详细介绍基于大模型的场景化GUI测试项目的执行逻辑，分析各个模块之间的交互模式。本文档适用于希望理解项目结构和执行流程的开发人员，通过阅读本文档，您将了解测试的具体步骤、各个模块的功能以及它们是如何协同工作的。

#### 1. 项目概述

本项目的主要目标是实现一个自动化的应用程序测试系统，该系统通过结合大语言模型（LLM）和图像识别技术来完成对移动应用的GUI操作测试。项目核心模块包括以下几个部分：
- **设备管理模块（DeviceManager）**：与移动设备交互，获取屏幕截图，执行触摸、输入等操作。
- **测试代理（TestAgent）**：负责控制测试的整体流程，调用其他模块完成从决策、执行到监督的整个测试循环。
- **观察者（Observer）**：检测应用界面上的GUI元素。
- **执行者（ActionExecutor）**：根据给定的操作执行对设备的具体操作。
- **决策者（ActionDecider）**：根据当前状态和历史操作决定下一步操作。
- **监督者（TestSupervisor）**：负责检查操作效果，确定是否执行成功或需要进一步纠正。
- **记录器（TestRecorder）**：记录测试过程中产生的操作数据和日志，保存截图和测试脚本。

#### 2. 测试整体流程概览

测试流程的整体逻辑如下图所示：

```
┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐      ┌───────────┐
│ Initialize│ ──► │ Observing │ ──► │ Executing │ ──► │ Checking  │ ──► │ Correcting │
└───────────┘      └───────────┘      └───────────┘      └───────────┘      └───────────┘
      ▲                                                                                  │
      └──────────────────────────────────────────────────────────────────────────────────┘
```

1. **初始化（Initialize）**：设置应用信息、启动测试环境。
2. **观察（Observing）**：捕捉屏幕截图，检测界面元素，确定当前应用状态。
3. **执行（Executing）**：根据决策者的指令，执行对应用的交互操作。
4. **检查（Checking）**：验证操作的效果，确认是否达到预期目标。
5. **纠正（Correcting）**：在操作失败时，调整策略或返回到上一步，重新尝试操作。

#### 3. 各模块功能与交互

#### 3.1. 主入口逻辑

在 `main` 函数中，测试流程的入口被定义：

```python
if __name__ == "__main__":
    os.environ["PATH"] += ":/opt/android/sdk/platform-tools"

    device = Device()
    base_dir = os.path.dirname(__file__)
    dm = DeviceManager(device=device, base_dir=base_dir)
    agent = TestAgent(device_manager=dm, base_dir=base_dir)
    agent.initialize(app_id="A104", scenario_id="S9")

    print("Please open the app and direct it to the initial page of the scenario.")
    input("Press enter to start the test...")

    while agent.state != "FAILED" and agent.state != "END" and agent.state != "ERROR":
        agent.step()
```

此代码完成以下几项工作：
1. **设置环境变量**：将Android SDK工具加入环境变量，确保后续能调用ADB等命令。
2. **实例化设备管理器（DeviceManager）**：通过 `Device` 对象管理测试设备。
3. **实例化测试代理（TestAgent）**：启动主控逻辑，包括初始化、执行步骤等。
4. **初始化应用和场景**：配置应用ID和测试场景ID，将设备设置到测试的初始页面。
5. **进入测试循环**：在测试代理 `TestAgent` 运行状态未结束的情况下，不断执行测试步骤。

#### 3.2. 设备管理器（DeviceManager）

设备管理器负责控制实际的移动设备操作，它包括以下功能：
- 获取设备的截图。
- 执行触摸、输入等操作。
- 启动和关闭应用程序。

通过与 `TestAgent` 的交互，设备管理器能够执行各种指令，比如模拟点击、滚动、输入等操作。

#### 3.3. 测试代理（TestAgent）

`TestAgent` 是整个测试流程的核心调度器，管理着其他各个模块的操作。其主要逻辑流程如下：

1. **初始化（Initialize）**：`initialize` 方法被调用，加载应用程序和场景配置，并启动应用程序到预期的初始页面。
2. **状态流转**：`step` 方法根据当前状态执行不同的操作，状态流转如下：
    - **`UNINITIALIZED`**：初始化未完成，系统输出警告。
    - **`INITIALIZED`**：开始观察（`Observing`）状态，抓取初始界面信息。
    - **`OBSERVING`**：使用 `Observer` 捕捉截图并检测元素，生成后续操作。
    - **`EXECUTING`**：`ActionExecutor` 根据已决定的操作执行具体操作。
    - **`LOAD-CHECKING`**：`TestSupervisor` 验证是否加载成功，如失败则尝试等待。
    - **`EFFECT-CHECKING`**：检查操作效果是否达到预期。
    - **`CORRECTING`**：当操作失效时，`TestAgent` 会纠正操作，重新进行尝试。
    - **`END` 或 `FAILED`**：测试结束或失败时，输出日志并停止执行。

#### 3.4. 观察者（Observer）

`Observer` 模块负责捕获设备当前界面的截图，并调用 `WidgetDetector` 检测应用界面上的GUI元素。它会根据当前屏幕内容生成标记图像，以帮助 `ActionDecider` 做出合理的操作判断。

**流程**：
- 获取屏幕截图。
- 使用 `WidgetDetector` 识别界面上的可交互元素，并生成截图带有的边界框。
- 返回识别结果，供 `TestAgent` 和 `ActionDecider` 使用。

#### 3.5. 执行者（ActionExecutor）

`ActionExecutor` 负责将 `ActionDecider` 决定的操作实际应用到设备上。根据具体操作类型（如 `touch`、`input`、`scroll`、`back` 等），它会调用 `DeviceManager` 来完成操作，并记录结果。

例如，当一个操作指示点击屏幕某处时，`ActionExecutor` 会计算出点击位置的坐标，并让设备管理器执行点击操作。每一个操作执行后，都会记录到 `TestRecorder` 中，以便后续分析。

#### 3.6. 决策者（ActionDecider）

`ActionDecider` 的核心职责是根据当前的界面状态和之前的操作历史，决定下一步的操作。这个模块会通过与大语言模型（如 GPT-4）的交互来获取指导意见。具体流程如下：
- 从 `Memory` 中提取当前界面状态和历史操作。
- 根据屏幕截图和上下文信息，与大模型交互生成操作决策。
- 如果需要，进一步验证操作是否有效，并返回最终决策。

#### 3.7. 监督者（TestSupervisor）

`TestSupervisor` 用于检查操作的效果，判断当前操作是否有效。例如，在执行了“点击按钮”的操作后，`TestSupervisor` 会检查应用界面是否发生了预期的变化，并据此确认操作是否成功。如果操作失败，还会触发错误纠正流程。

#### 3.8. 记录器（TestRecorder）

`TestRecorder` 负责记录每一步操作的执行结果，包括生成的操作脚本、截图和上下文日志。通过记录器的保存，开发者可以在测试结束后重放操作，以便进行问题分析和调试。

### 4. 总结

基于大模型的场景化GUI测试系统，通过模块化设计，实现了自动化应用测试的整体闭环。各模块之间的交互逻辑如下图所示：

```
┌─────────────┐       ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ DeviceManager│◄───►│  TestAgent   │◄───►│   Observer    │◄───►│   ActionDecider │
└─────────────┘       └──────────────┘       └──────────────┘       └──────────────┘
        ▲                   ▲                      ▲                     ▲
        │                   │                      │                     │
        └───────────────────┴──────────────────────┴─────────────────────┘
```

通过上述模块的紧密合作，本系统能够智能化地执行应用测试，从初始化、观察、操作到效果验证，再到错误修正形成了一整套自动化流程。这不仅减少了人工

干预，还提高了测试效率和准确性。在大模型的引导下，系统能够动态适应应用界面变化，提升了测试的智能化程度。
## 流程概况
- 大概写了一个流程，不太完整，可供参考
好的，我会重新整理，并详细概述各个模块之间的交互逻辑及其如何协调工作，以便让整体测试流程更加清晰。

### 项目总体概述

本项目实现了一个基于大语言模型的场景化 GUI 测试系统，整个系统通过模拟用户操作、检测界面变化、执行设备指令来自动化测试应用。核心模块包括：

- **`TestAgent`（测试代理）**：主控流程的核心，负责状态流转和模块间的协调。
- **`DeviceManager`（设备管理）**：与物理设备交互的模块，实现截图、触摸、输入、滚动等操作。
- **`Observer`（观察者）**：捕捉屏幕截图并检测界面上的可交互元素。
- **`ActionDecider`（决策者）**：调用大语言模型，根据当前界面和场景，决定下一步操作。
- **`ActionExecutor`（执行者）**：基于决策结果，向设备发送指令，执行具体操作。
- **`TestRecorder`（记录器）**：记录操作历史，生成操作脚本和日志。
- **`TestSupervisor`（监督者）**：监控操作效果，验证操作是否达到预期。

### 各模块交互流程

#### 1. 流程初始化

1. **主流程 `main` 调用 `TestAgent.initialize`**：
   - 通过 `DeviceManager` 启动设备应用程序。
   - 读取配置的应用 ID 和场景 ID 以确定测试目标。
   - `Observer` 捕获初始屏幕截图，`TestAgent` 将状态设置为 `INITIALIZED`。

#### 2. 状态流转控制：`TestAgent`

`TestAgent` 是整个流程的主控模块，控制着状态流转和模块调用。执行流程通过调用 `step` 方法逐步推进，并根据不同的状态进行不同操作：

1. **状态 `INITIALIZED` → `OBSERVING`**：
   - `TestAgent` 调用 `Observer.capture_screenshot` 捕获当前屏幕截图。
   - 识别出当前界面的所有可交互元素，状态切换到 `OBSERVING`。

2. **状态 `OBSERVING`**：
   - 调用 `ActionDecider.next_action`，通过大模型分析界面和场景，决定下一步操作。
   - `Observer.detect_widgets` 检测界面上的可交互元素，结合模型决策确定具体操作目标。
   - `TestAgent` 切换到 `EXECUTING` 状态。

3. **状态 `EXECUTING`**：
   - `TestAgent` 调用 `ActionExecutor.execute` 执行 `ActionDecider` 决策的操作。
   - 具体操作通过 `DeviceManager` 控制物理设备（如触摸、输入、滚动等）。
   - 执行完操作后，`TestAgent` 切换到 `LOAD-CHECKING` 状态。

4. **状态 `LOAD-CHECKING`**：
   - `TestSupervisor.check_loading` 检查当前界面是否在加载（例如，等待应用响应）。
   - 如果应用仍在加载，则调用 `ActionExecutor` 发送等待指令，执行一个等待动作并重新检测。
   - 如果确认加载完成，状态切换到 `EFFECT-CHECKING`。

5. **状态 `EFFECT-CHECKING`**：
   - 通过 `TestSupervisor.check_effect` 确认操作的效果是否符合预期。
   - 若效果符合预期，切换到 `END-CHECKING` 状态。
   - 若效果不符合预期，切换到 `CORRECTING` 状态，进行错误处理。

6. **状态 `CORRECTING`**：
   - 调用 `ActionDecider.issue_feedback` 获取具体问题并决定如何修正。
   - 如果操作目标不匹配，通过 `ActionDecider.rematch_next_action` 重试识别并执行。
   - 如修正无效超过一定次数，则状态设置为 `FAILED`。
   - 如果修正有效，执行成功，状态切换回 `EXECUTING`，重新执行操作。

7. **状态 `END-CHECKING`**：
   - 调用 `TestSupervisor.check_end` 判断测试是否结束。
   - 若测试已完成，`TestAgent` 状态设置为 `END`，生成完整的测试记录。

### 3. 模块之间的具体调用关系

1. **`TestAgent` 与 `DeviceManager`**：
   - `TestAgent` 使用 `DeviceManager` 启动应用、发送触摸、滚动等操作。
   - 设备状态变化（如窗口、焦点）实时反馈到 `Memory` 中，作为后续操作的参考。

2. **`TestAgent` 与 `Observer`**：
   - `Observer` 负责从设备中获取截图，并使用 `WidgetDetector` 检测屏幕中的可操作元素。
   - `TestAgent` 通过 `Observer` 更新 `Memory` 中的界面状态，决定下一步操作。

3. **`TestAgent` 与 `ActionDecider`**：
   - `ActionDecider` 基于 `Memory` 中的状态调用大语言模型，分析界面和操作历史，决策下一个动作。
   - `TestAgent` 调用 `ActionDecider.confirm_next_action` 进一步确认操作的有效性。

4. **`ActionExecutor` 和 `DeviceManager`**：
   - `ActionExecutor` 将 `ActionDecider` 决定的操作转化为设备指令，通过 `DeviceManager` 控制设备。
   - 例如，确定坐标并模拟点击、输入、滚动等操作。

5. **`TestSupervisor` 检查与修正**：
   - `TestSupervisor.check_loading`、`check_effect` 等方法用于检查操作是否成功。
   - 如果操作不成功，则会通知 `ActionDecider` 进行修正。
   - 通过 `ActionDecider.rematch_next_action` 或 `next_action` 重新生成有效的操作。

6. **`TestRecorder` 记录操作**：
   - 在每次操作执行后，`TestAgent` 调用 `TestRecorder.record` 记录该操作。
   - 生成详细的操作日志和脚本，以便后续回顾和分析。

### 4. 流程详细示例

1. **初始阶段**：
   - `TestAgent` 启动应用，`Observer` 捕捉初始截图。
   - 识别界面元素并进入 `OBSERVING` 状态。

2. **决策阶段**：
   - `ActionDecider` 调用大模型，分析界面、生成操作：
     - 例如：用户需要点击一个登录按钮。
   - `Observer` 识别界面上的按钮元素，`ActionDecider` 确认决策，并进入 `EXECUTING`。

3. **执行阶段**：
   - `ActionExecutor` 通过 `DeviceManager` 控制设备模拟点击操作。
   - 执行后，更新 `Memory` 记录，并进入 `LOAD-CHECKING`。

4. **效果验证**：
   - `TestSupervisor.check_loading` 确认页面是否加载完成。
   - 确认完成后，通过 `check_effect` 检查操作效果。
   - 如果效果不符，`ActionDecider` 进行问题分析和修正，再次执行。

5. **结束**：
   - 当 `TestSupervisor.check_end` 判断测试结束时，`TestRecorder` 生成完整的操作日志，记录此次测试。


- 还要录视频