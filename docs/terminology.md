# 术语表

## 核心术语

| 术语 | 定义 |
|------|------|
| **宏 (Macro)** | 录制的或编写的鼠标/键盘操作序列，用于自动化 |
| **脚本 (Script)** | YAML 文件，定义宏的元数据、配置、资源和动作 |
| **Python 脚本** | Python 文件，包含复杂自动化流程的逻辑 |
| **子脚本 (Sub-script)** | 被另一个脚本调用的脚本（层级执行） |
| **检测区域 (Detection Zone)** | 用于图像识别的截图区域 |

## 模块术语

| 术语 | 定义 |
|------|------|
| **ScreenManager** | 核心模块：窗口管理和截图 |
| **InputController** | 核心模块：鼠标键盘模拟 |
| **ImageMatcher** | 核心模块：模板匹配图像识别 |
| **ConfigManager** | 核心模块：YAML 脚本加载 |
| **MacroLogger** | 核心模块：日志和执行报告 |
| **ScriptExecutor** | 模块：执行脚本并提供 Python API |
| **ScriptRecorder** | 模块：录制用户输入生成脚本 |
| **ZoneCaptor** | 模块：捕获检测区域截图 |

## 动作类型

| 动作 | 定义 |
|------|------|
| **click** | 在指定坐标点击鼠标 |
| **click_image** | 在图像位置点击（模板匹配） |
| **keypress** | 键盘按键 |
| **type_text** | 键盘文本输入 |
| **delay** | 等待指定毫秒数 |
| **wait_image** | 等待图像出现在屏幕上 |
| **wait_image_disappear** | 等待图像从屏幕消失 |
| **move_mouse** | 移动鼠标到指定坐标 |
| **scroll** | 滚动鼠标滚轮 |
| **log** | 记录日志消息 |
| **run_script** | 执行子脚本 |

## 配置术语

| 术语 | 定义 |
|------|------|
| **window_title** | 目标游戏窗口的标题 |
| **screenshot_size** | 每次点击时截图的大小（默认 400x400） |
| **scale_factor** | 不同分辨率间坐标缩放的比例 |
| **log_level** | 日志级别：DEBUG、INFO、WARNING、ERROR |
| **on_error** | 错误处理策略：stop、retry、ignore |
| **retry_times** | 错误发生时重试次数 |
| **default_timeout** | wait_image 操作的默认超时时间（毫秒） |
| **confidence** | 图像匹配置信度阈值（0.0-1.0） |

## 录制术语

| 术语 | 定义 |
|------|------|
| **录制 (Recording)** | 捕获用户输入以生成脚本的过程 |
| **InputRecorder** | 监听鼠标/键盘事件的组件 |
| **RecordedAction** | 捕获的单个动作的数据结构 |
| **offset** | 当图像匹配失败时，作为备用的屏幕坐标 |

## 执行术语

| 术语 | 定义 |
|------|------|
| **执行 (Execution)** | 运行脚本以自动化游戏操作的过程 |
| **执行报告 (Execution Report)** | 脚本执行摘要，包含时长、状态、错误 |
| **loop_count** | 当前循环的迭代次数 |

## 图像识别术语

| 术语 | 定义 |
|------|------|
| **模板匹配 (Template Matching)** | 在较大图像中查找模板图像 |
| **置信度 (Confidence)** | 匹配图像之间的相似度分数（0.0-1.0） |
| **区域 (Region)** | 图像搜索的边界框 [x, y, width, height] |

## 项目结构术语

| 术语 | 定义 |
|------|------|
| **assets/templates** | 动作模板图片目录 |
| **assets/detection** | 检测区域图片目录 |
| **scripts/** | 用户脚本目录（YAML + Python） |
| **logs/** | 执行日志和报告目录 |