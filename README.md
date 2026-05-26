# Game Macro Automation

游戏宏自动化系统 - 基于 Python 的 Windows 游戏宏工具

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 功能特性

- **录制生成**: 录制鼠标键盘操作，生成基础单元脚本
- **Python 编排**: 使用 Python 编写复杂流程逻辑（循环、条件、子脚本调用）
- **图像识别**: pyautogui 模板匹配，自动 UI 定位
- **分辨率适配**: 自动检测窗口分辨率，计算缩放因子
- **层级调用**: 脚本可调用其他脚本，形成层级结构
- **详细日志**: 可配置日志等级，执行报告生成
- **F12 热键**: 录制时按 F12 停止

## 快速开始

### 1. 安装

```bash
# 克隆项目
git clone <repository-url>
cd GameMacroAutomation

# 安装依赖
pip install -r requirements.txt
```

### 2. 录制脚本

```bash
# 录制脚本（自动全屏截图）
python -m src.main record -o scripts/test.yaml

# 指定截图区域大小（默认 400x400）
python -m src.main record -o scripts/test.yaml -s 600

# 录制时按 F12 停止，或 Ctrl+C 强制退出
```

### 3. 运行脚本

```bash
# 运行脚本
python -m src.main run scripts/test.yaml
```

### 4. 其他命令

```bash
# 截图检测区域
python -m src.main capture-zone --output assets/detection/boss_hp.png

# 验证脚本
python -m src.main validate scripts/test.yaml

# 显示脚本依赖树
python -m src.main tree scripts/entry_dungeon.yaml

# 列出可用脚本
python -m src.main list
```

## 脚本示例

### YAML + Python 混合方案

```yaml
# scripts/attack.yaml
meta:
  name: "攻击动作"
  version: "1.0"

config:
  log_level: "INFO"

assets:
  images:
    target: "assets/attack_btn.png"

python_script: "attack.py"
```

```python
# scripts/attack.py
def main(executor):
    executor.log("开始攻击", "INFO")
    
    # 等待图片出现
    if not executor.wait_image("target", 3000):
        executor.log("未找到目标", "ERROR")
        return False
    
    # 点击图片
    executor.click_image("target")
    executor.delay(200)
    
    return True
```

## 示例项目

查看 `docs/examples/` 目录获取完整示例：

| 示例 | 难度 | 功能 |
|------|------|------|
| [01_loop_demo](docs/examples/01_loop_demo/README.md) | ⭐ 入门 | `loop_while` 条件循环，子脚本调用 |
| [02_battle_example](docs/examples/02_battle_example/README.md) | ⭐⭐ 进阶 | 多阶段战斗，多种循环控制 |

### 运行示例

```bash
# 示例 1: 循环控制
python -m src.main run docs/examples/01_loop_demo/main.yaml

# 示例 2: 战斗流程
python -m src.main run docs/examples/02_battle_example/battle_loop.yaml
```

## Python 脚本 API

### 图像识别

```python
executor.click_image("attack_btn", confidence=0.8)  # 点击图片
executor.image_exists("boss_hp_bar")                # 检查图片是否存在
executor.wait_image("start_btn", timeout=5000)      # 等待图片出现
```

### 循环控制

```python
# 条件循环
executor.loop_while(
    condition=lambda: executor.image_exists("boss_hp_bar"),
    body=lambda: executor.click_image("attack_btn") or executor.delay(1000),
    max_iterations=100,
    interval=1000
)

# 固定次数循环
executor.loop_times(5, lambda: executor.click_image("item_1"), delay_ms=200)

# 直到条件满足
executor.loop_until(
    condition=lambda: executor.image_exists("reward_popup"),
    body=lambda: executor.click_image("collect_btn"),
    timeout=30000
)
```

### 脚本控制

```python
executor.run_script("potion.yaml")    # 运行子脚本
executor.delay(1000)                  # 延迟 1 秒
executor.log("战斗开始", "INFO")       # 日志记录
```

### 图标状态监测

```python
# 监听图标状态变化，检测到变化时执行回调并播放声音
changed, coords = executor.monitor_icon_state(
    region={"x": (0.4, 0.6), "y": (0.1, 0.2)},  # 检测区域
    normal_template="icon_normal",              # 正常状态模板
    color_mode="color",                         # 颜色对比模式
    color_diff_threshold=0.15,                  # 颜色差异阈值
    interval_ms=500,                            # 检测间隔
    timeout=60000,                              # 超时时间
    on_changed=lambda state: executor.log(f"图标状态变化: {state}"),
    sound={"type": "system"}                    # 变化时播放声音
)
```

**color_mode 模式说明：**

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `template` | 传统模板匹配 | 简单场景 |
| `histogram` | 颜色直方图对比 | 颜色变化明显 |
| `color` | Alpha 通道提取颜色（推荐） | 同形异色图标 |

### 声音提醒

```python
# 播放系统提示音
executor.play_sound({"type": "system"})

# 播放音频文件
executor.play_sound({"type": "file", "file": "alert.wav"})
```

## 项目结构

```
game-macro-automation/
├── src/
│   ├── core/           # 核心模块（屏幕、输入、图像、配置、日志）
│   ├── recorder/       # 录制器
│   ├── executor/       # 执行器
│   ├── script/         # 脚本验证和管理
│   └── tools/          # 辅助工具（截图工具）
├── docs/
│   ├── design/         # 设计文档
│   │   ├── core/README.md
│   │   ├── recorder/README.md
│   │   ├── executor/README.md
│   │   ├── script/README.md
│   │   └── tools/README.md
│   └── examples/       # 示例项目
├── scripts/            # 用户脚本目录
└── assets/             # 图片资源
    ├── templates/      # 动作模板
    └── detection/      # 检测区域
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/
```

## 依赖

### 核心依赖

- `pyautogui` - 鼠标键盘模拟、图像识别
- `pynput` - 输入监听
- `Pillow` - 图像处理
- `pyyaml` - YAML 解析
- `pygetwindow` - 窗口管理

### 开发依赖

- `pytest` - 测试框架
- `black` - 代码格式化
- `ruff` - 代码检查
- `mypy` - 类型检查

## 文档

| 文档 | 说明 |
|------|------|
| [设计文档](docs/design/README.md) | 系统架构和模块设计 |
| [Python 脚本使用指南](docs/python_script_guide.md) | Python 脚本 API 和示例 |
| [示例项目](docs/examples/README.md) | 完整示例代码 |

### 模块设计文档

- [Core 模块](docs/design/core/README.md) - 屏幕、输入、图像、配置、日志
- [Recorder 模块](docs/design/recorder/README.md) - 录制器
- [Executor 模块](docs/design/executor/README.md) - 执行器、Python 脚本 API
- [Script 模块](docs/design/script/README.md) - 脚本验证
- [Tools 模块](docs/design/tools/README.md) - 截图工具

## 常见问题

### Q: 录制时截图全黑怎么办？

A: 可能是因为窗口被最小化或遮挡。确保窗口可见且在前台。如果问题持续，尝试：
1. 增大截图尺寸：`-s 600`
2. 使用全屏坐标截图（自动 fallback）

### Q: 如何调整截图区域大小？

A: 使用 `-s` 或 `--screenshot-size` 参数：
```bash
python -m src.main record -o scripts/test.yaml -s 600
```

### Q: 图像识别失败怎么办？

A: 尝试以下方法：
1. 降低置信度：`executor.click_image("btn", confidence=0.6)`
2. 重新录制，确保点击位置准确
3. 使用更大的截图区域

### Q: 如何停止录制？

A: 按 `F12` 键正常停止，或 `Ctrl+C` 强制退出。

## 许可证

Apache-2.0 license
