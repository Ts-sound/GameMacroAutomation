# Game Macro Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建基于 Python + Lua 的 Windows 游戏宏自动化系统，支持录制、Lua 编排、图像识别、截图工具和完整日志系统。

**Architecture:** YAML+Lua 混合方案 - YAML 存储配置/资源，Lua 编写流程逻辑。采用统一脚本架构，所有脚本都是单元脚本，支持层级调用。

**Tech Stack:** Python 3.10+, PyYAML, OpenCV, pyautogui, pynput, PyGetWindow, lupa (Lua 嵌入), pydantic

**MVP 范围:** 基础功能 (录制/执行/图像识别) + 截图工具 + 高级编排 (Lua 条件/循环) + 日志系统

---

## 方案选型决策

### 1. 核心架构选型

| 组件 | 选型 | 理由 | 备选 |
|------|------|------|------|
| **主语言** | Python 3.10+ | 生态丰富，开发效率高 | - |
| **目标平台** | Windows only | 简化实现，专注 Windows 游戏 | 后续扩展跨平台 |
| **脚本格式** | YAML | 人类可读，易编辑 | JSON, TOML |
| **编排引擎** | Lua (嵌入) | 轻量、易嵌入、热重载 | 纯 Python 解释器 |
| **输入控制** | pyautogui + pynput | 成熟稳定，API 简单 | 直接 Win32 API |
| **图像识别** | OpenCV 模板匹配 | 简单快速，适合固定 UI | 特征匹配、深度学习 |
| **窗口管理** | PyGetWindow | 跨窗口获取和定位 | Win32 GUI |
| **配置管理** | PyYAML + pydantic | 类型验证 + 易用性 | 纯 PyYAML |

### 2. 技术栈详细说明

```python
# 核心依赖
pyautogui>=0.9.54      # 鼠标键盘模拟
pynput>=1.7.6          # 输入事件监听
opencv-python>=4.8.0   # 图像识别
numpy>=1.24.0          # 数组处理
Pillow>=10.0.0         # 图像处理
pyyaml>=6.0            # YAML 解析
pygetwindow>=0.0.9     # 窗口管理
lupa>=2.0              # Lua 嵌入 (用于编排引擎)
pydantic>=2.0          # 配置验证 (可选)
```

### 3. 架构调整建议

根据选型，原设计需要以下调整：

#### 3.1 脚本执行引擎
- **原设计**: 纯 Python 解释器
- **新设计**: Lua 嵌入作为编排引擎，Python 提供底层 API
- **优势**: 
  - Lua 轻量，启动快
  - 支持热重载脚本
  - 与 Python 隔离，脚本错误不影响主程序
  - Lua 语法简洁，适合编写流程逻辑

#### 3.2 YAML + Lua 混合方案
```yaml
# 脚本定义 (YAML) - 数据层
meta:
  name: "副本流程"
  version: "1.0"

config:
  window_title: "游戏窗口"
  log_level: "INFO"

assets:
  images:
    attack_btn: "assets/attack_btn.png"

# Lua 脚本引用
lua_script: "scripts/dungeon_flow.lua"
```

```lua
-- 流程逻辑 (Lua) - 逻辑层
-- dungeon_flow.lua

function main()
    -- 进入战斗
    run_script("attack.yaml")
    
    -- 战斗循环
    local max_iterations = 100
    for i = 1, max_iterations do
        if not image_exists("boss_hp_bar") then
            break
        end
        
        -- 检查血量
        if image_exists("low_hp_warning") then
            run_script("potion.yaml")
        else
            run_script("skill1.yaml")
        end
        
        delay(1000)
    end
    
    -- 领取奖励
    if image_exists("reward_popup") then
        run_script("collect_reward.yaml")
    else
        log("No reward popup found", "WARNING")
    end
end
```

#### 3.3 Python-Lua 桥接
```python
# Python 提供底层 API 给 Lua 调用
class LuaBridge:
    def __init__(self, executor):
        self.executor = executor
    
    def register_functions(self, lua_state):
        lua_state.globals()['click_image'] = self.click_image
        lua_state.globals()['image_exists'] = self.image_exists
        lua_state.globals()['run_script'] = self.run_script
        lua_state.globals()['delay'] = self.delay
        lua_state.globals()['log'] = self.log
    
    def click_image(self, image_name: str, confidence: float = 0.9):
        # 调用 Python 图像识别和输入
        ...
    
    def image_exists(self, image_name: str) -> bool:
        # 检查图像是否存在
        ...
```

---

## 项目结构

```
game-macro-automation/
├── README.md
├── docs/
│   ├── DESIGN.md              # 设计文档
│   └── plans/                 # 实施计划
│
├── requirements.txt           # Python 依赖
├── requirements-dev.txt       # 开发依赖
├── pyproject.toml            # 项目配置
├── config.yaml               # 全局配置
│
├── src/
│   ├── __init__.py
│   ├── main.py               # CLI 入口
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── screen.py         # 屏幕捕捉 + 窗口管理
│   │   ├── input.py          # 输入控制 (pyautogui + pynput)
│   │   ├── image.py          # 图像识别 (OpenCV)
│   │   ├── lua_bridge.py     # Python-Lua 桥接
│   │   └── config.py         # 配置管理
│   │
│   ├── recorder/
│   │   ├── __init__.py
│   │   ├── recorder.py       # 录制器
│   │   └── preview.py        # 录制预览
│   │
│   ├── executor/
│   │   ├── __init__.py
│   │   ├── executor.py       # Lua 执行器
│   │   ├── yaml_parser.py    # YAML 解析
│   │   └── runner.py         # 动作执行
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   └── zone_captor.py    # 检测区域截图工具
│   │
│   └── script/
│       ├── __init__.py
│       ├── schema.py         # YAML schema
│       └── validator.py      # 脚本验证
│
├── scripts/                  # 脚本目录
│   ├── entry_dungeon.yaml
│   ├── entry_dungeon.lua
│   ├── attack.yaml
│   └── ...
│
├── assets/
│   ├── templates/            # 动作模板图片
│   └── detection/            # 条件检测图片
│
├── logs/                     # 日志目录
│
└── tests/
    ├── __init__.py
    ├── test_screen.py
    ├── test_input.py
    ├── test_image.py
    ├── test_lua_bridge.py
    └── test_executor.py
```

---

## 实施任务分解

### Task 1: 项目骨架搭建

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `src/__init__.py`
- Create: `src/main.py`
- Create: `src/core/__init__.py`
- Create: `src/recorder/__init__.py`
- Create: `src/executor/__init__.py`
- Create: `src/tools/__init__.py`
- Create: `src/script/__init__.py`
- Create: `tests/__init__.py`
- Create: `README.md`

**Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "game-macro-automation"
version = "0.1.0"
description = "游戏宏自动化系统 - 基于 Python + Lua"
requires-python = ">=3.10"
dependencies = [
    "pyautogui>=0.9.54",
    "pynput>=1.7.6",
    "opencv-python>=4.8.0",
    "numpy>=1.24.0",
    "Pillow>=10.0.0",
    "pyyaml>=6.0",
    "pygetwindow>=0.0.9",
    "lupa>=2.0",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[project.scripts]
gma = "src.main:cli"

[tool.black]
line-length = 88
target-version = ["py310"]

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "I"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
```

**Step 2: 创建 requirements.txt**

```txt
pyautogui>=0.9.54
pynput>=1.7.6
opencv-python>=4.8.0
numpy>=1.24.0
Pillow>=10.0.0
pyyaml>=6.0
pygetwindow>=0.0.9
lupa>=2.0
pydantic>=2.0
```

**Step 3: 创建 requirements-dev.txt**

```txt
pytest>=7.0
pytest-cov>=4.0
black>=23.0
ruff>=0.1.0
mypy>=1.0
```

**Step 4: 创建 src/main.py (CLI 入口)**

```python
"""游戏宏自动化 - CLI 入口"""
import argparse
import sys


def cli():
    parser = argparse.ArgumentParser(
        description="游戏宏自动化系统",
        prog="gma"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # record 命令
    record_parser = subparsers.add_parser("record", help="录制宏脚本")
    record_parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出 YAML 文件路径"
    )
    record_parser.add_argument(
        "--window", "-w",
        help="游戏窗口标题 (可选，自动检测)"
    )
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行宏脚本")
    run_parser.add_argument(
        "script",
        help="YAML 脚本文件路径"
    )
    run_parser.add_argument(
        "--window", "-w",
        help="游戏窗口标题 (覆盖脚本配置)"
    )
    run_parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志等级"
    )
    
    # capture-zone 命令
    capture_parser = subparsers.add_parser(
        "capture-zone",
        help="截图检测区域"
    )
    capture_parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出图片路径"
    )
    
    # validate 命令
    validate_parser = subparsers.add_parser(
        "validate",
        help="验证脚本格式"
    )
    validate_parser.add_argument(
        "script",
        help="YAML 脚本文件路径"
    )
    
    # list 命令
    subparsers.add_parser("list", help="列出可用脚本")
    
    # tree 命令
    tree_parser = subparsers.add_parser(
        "tree",
        help="显示脚本依赖树"
    )
    tree_parser.add_argument(
        "script",
        help="YAML 脚本文件路径"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # 根据命令调用对应模块
    if args.command == "record":
        from src.recorder.recorder import record_script
        record_script(args.output, args.window)
    elif args.command == "run":
        from src.executor.executor import run_script
        run_script(args.script, args.window, args.log_level)
    elif args.command == "capture-zone":
        from src.tools.zone_captor import capture_zone
        capture_zone(args.output)
    elif args.command == "validate":
        from src.script.validator import validate_script_file
        validate_script_file(args.script)
    elif args.command == "list":
        from src.script.manager import list_scripts
        list_scripts()
    elif args.command == "tree":
        from src.script.manager import show_script_tree
        show_script_tree(args.script)


if __name__ == "__main__":
    cli()
```

**Step 5: 创建 README.md**

```markdown
# Game Macro Automation

游戏宏自动化系统 - 基于 Python + Lua 的 Windows 游戏宏工具

## 功能特性

- **录制生成**: 录制鼠标键盘操作，生成基础单元脚本
- **Lua 编排**: 使用 Lua 编写复杂流程逻辑
- **图像识别**: OpenCV 模板匹配，自动 UI 定位
- **分辨率适配**: 自动检测窗口分辨率，计算缩放因子
- **层级调用**: 脚本可调用其他脚本，形成层级结构
- **详细日志**: 可配置日志等级，执行报告生成

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 录制脚本

```bash
python -m src.main record --output scripts/attack.yaml
```

### 运行脚本

```bash
python -m src.main run scripts/entry_dungeon.yaml
```

### 截图检测区域

```bash
python -m src.main capture-zone --output assets/detection/boss_hp.png
```

## 脚本示例

### YAML 配置 (attack.yaml)

```yaml
meta:
  name: "攻击动作"
  version: "1.0"

config:
  window_title: "游戏窗口"
  log_level: "INFO"

assets:
  images:
    target: "assets/attack_btn.png"

lua_script: "scripts/attack.lua"
```

### Lua 逻辑 (attack.lua)

```lua
function main()
    wait_image("target", 3000)
    click_image("target")
    delay(200)
end
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
```

**Step 6: 创建空 __init__.py 文件**

```python
# src/__init__.py
"""游戏宏自动化系统"""
__version__ = "0.1.0"

# src/core/__init__.py
from .screen import ScreenManager
from .input import InputController
from .image import ImageMatcher
from .lua_bridge import LuaBridge
from .config import ConfigManager

__all__ = [
    "ScreenManager",
    "InputController",
    "ImageMatcher",
    "LuaBridge",
    "ConfigManager",
]

# src/recorder/__init__.py
from .recorder import ScriptRecorder

__all__ = ["ScriptRecorder"]

# src/executor/__init__.py
from .executor import ScriptExecutor

__all__ = ["ScriptExecutor"]

# src/tools/__init__.py
# src/script/__init__.py
# tests/__init__.py
```

**Step 7: 验证项目骨架**

```bash
# 检查项目结构
tree -L 3

# 尝试导入
python -c "import src; print(src.__version__)"

# 运行 CLI 帮助
python -m src.main --help
```

**Step 8: 提交**

```bash
git add .
git commit -m "feat: 初始化项目骨架"
```

---

### Task 2: 核心模块 - ScreenManager

**Files:**
- Create: `src/core/screen.py`
- Create: `tests/test_screen.py`

**Step 1: 编写测试**

```python
# tests/test_screen.py
import pytest
from src.core.screen import ScreenManager


class TestScreenManager:
    def test_find_window_by_title(self):
        """测试窗口查找"""
        manager = ScreenManager()
        # 使用记事本作为测试窗口
        window = manager.find_window("Untitled - Notepad")
        assert window is not None
        assert window.title == "Untitled - Notepad"
        assert window.width > 0
        assert window.height > 0
    
    def test_get_window_size(self):
        """测试获取窗口尺寸"""
        manager = ScreenManager()
        window = manager.find_window("Untitled - Notepad")
        width, height = manager.get_window_size(window)
        assert width > 0
        assert height > 0
    
    def test_calculate_scale_factor(self):
        """测试缩放因子计算"""
        manager = ScreenManager()
        reference = (1920, 1080)
        current = (1280, 720)
        scale = manager.calculate_scale_factor(current, reference)
        assert scale == pytest.approx(0.666, rel=0.01)
    
    def test_capture_window_region(self):
        """测试窗口区域截图"""
        manager = ScreenManager()
        window = manager.find_window("Untitled - Notepad")
        # 截取窗口左上角 100x100 区域
        image = manager.get_screen_region(window, 0, 0, 100, 100)
        assert image is not None
        assert image.width == 100
        assert image.height == 100
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_screen.py -v
# Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.screen'"
```

**Step 3: 实现 ScreenManager**

```python
# src/core/screen.py
"""屏幕捕捉和窗口管理模块"""
from dataclasses import dataclass
from typing import Optional, Tuple
from PIL import Image
import pygetwindow as gw


@dataclass
class WindowInfo:
    """窗口信息"""
    title: str
    left: int
    top: int
    width: int
    height: int
    
    @property
    def right(self) -> int:
        return self.left + self.width
    
    @property
    def bottom(self) -> int:
        return self.top + self.height


class ScreenManager:
    """屏幕和窗口管理器"""
    
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """
        根据标题查找窗口
        
        Args:
            title: 窗口标题 (支持模糊匹配)
        
        Returns:
            WindowInfo 或 None
        """
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            return None
        
        # 返回第一个匹配的窗口
        window = windows[0]
        return WindowInfo(
            title=window.title,
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height
        )
    
    def get_window_size(self, window: WindowInfo) -> Tuple[int, int]:
        """获取窗口尺寸"""
        return (window.width, window.height)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        import screeninfo
        screens = screeninfo.get_monitors()
        if screens:
            return (screens[0].width, screens[0].height)
        return (1920, 1080)  # 默认
    
    def calculate_scale_factor(
        self,
        current_size: Tuple[int, int],
        reference_size: Tuple[int, int]
    ) -> float:
        """
        计算缩放因子
        
        Args:
            current_size: 当前窗口尺寸 (width, height)
            reference_size: 参考尺寸 (width, height)
        
        Returns:
            缩放因子 (0.0 - 1.0+)
        """
        curr_w, curr_h = current_size
        ref_w, ref_h = reference_size
        
        scale_x = curr_w / ref_w
        scale_y = curr_h / ref_h
        
        # 取较小值保证内容不超出
        return min(scale_x, scale_y)
    
    def get_screen_region(
        self,
        window: Optional[WindowInfo],
        x: int,
        y: int,
        w: int,
        h: int
    ) -> Image.Image:
        """
        截取屏幕区域
        
        Args:
            window: 窗口信息 (可选，如果不传则截取全屏)
            x, y: 相对窗口左上角的坐标
            w, h: 区域宽高
        
        Returns:
            PIL Image
        """
        from PIL import ImageGrab
        
        if window:
            # 截取窗口内的区域
            abs_x = window.left + x
            abs_y = window.top + y
        else:
            # 截取全屏区域
            abs_x = x
            abs_y = y
        
        # 确保坐标非负
        abs_x = max(0, abs_x)
        abs_y = max(0, abs_y)
        
        # 截取区域
        screenshot = ImageGrab.grab(bbox=(abs_x, abs_y, abs_x + w, abs_y + h))
        return screenshot
    
    def auto_detect_scale_factor(
        self,
        window_title: str,
        reference_resolution: Tuple[int, int] = (1920, 1080)
    ) -> Optional[float]:
        """
        自动检测缩放因子
        
        Args:
            window_title: 窗口标题
            reference_resolution: 参考分辨率
        
        Returns:
            缩放因子或 None (窗口未找到)
        """
        window = self.find_window(window_title)
        if not window:
            return None
        
        current_size = self.get_window_size(window)
        return self.calculate_scale_factor(current_size, reference_resolution)
```

**Step 4: 运行测试验证通过**

```bash
pytest tests/test_screen.py::TestScreenManager -v
# Expected: PASS (需要先打开记事本窗口)
```

**Step 5: 提交**

```bash
git add src/core/screen.py tests/test_screen.py
git commit -m "feat(core): 实现 ScreenManager 屏幕窗口管理"
```

---

### Task 3: 核心模块 - InputController

**Files:**
- Create: `src/core/input.py`
- Create: `tests/test_input.py`

**Step 1: 编写测试**

```python
# tests/test_input.py
import pytest
from unittest.mock import Mock, patch
from src.core.input import InputController, RecordedAction


class TestInputController:
    def test_click_at_position(self):
        """测试点击坐标"""
        controller = InputController()
        with patch('pyautogui.click') as mock_click:
            controller.click(100, 200, button='left')
            mock_click.assert_called_once_with(x=100, y=200, button='left')
    
    def test_key_press(self):
        """测试按键"""
        controller = InputController()
        with patch('pyautogui.press') as mock_press:
            controller.press('space')
            mock_press.assert_called_once_with('space')
    
    def test_delay(self):
        """测试延迟"""
        controller = InputController()
        with patch('time.sleep') as mock_sleep:
            controller.delay(100)  # 100ms
            mock_sleep.assert_called_once_with(0.1)
    
    def test_scale_coordinates(self):
        """测试坐标缩放"""
        controller = InputController()
        controller.scale_factor = 0.5
        scaled = controller.scale_coordinates(100, 200)
        assert scaled == (50, 100)


class TestRecordedAction:
    def test_action_creation(self):
        """测试录制动作创建"""
        action = RecordedAction(
            timestamp=1000,
            action_type="mouse_click",
            x=100,
            y=200,
            button="left"
        )
        assert action.timestamp == 1000
        assert action.x == 100
        assert action.y == 200
```

**Step 2: 实现 InputController**

```python
# src/core/input.py
"""输入控制模块 - 封装 pyautogui 和 pynput"""
import time
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

import pyautogui
from pynput import mouse, keyboard


class MouseButton(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


@dataclass
class RecordedAction:
    """录制的动作"""
    timestamp: int  # 相对时间 ms
    action_type: str  # mouse_click, key_press, mouse_move
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None
    key: Optional[str] = None
    window_title: Optional[str] = None


class InputController:
    """输入控制器 - 执行动作"""
    
    def __init__(self, scale_factor: float = 1.0):
        """
        Args:
            scale_factor: 坐标缩放因子
        """
        self.scale_factor = scale_factor
        # 配置 pyautogui
        pyautogui.FAILSAFE = True  # 鼠标移到屏幕角落触发故障保护
        pyautogui.PAUSE = 0.1  # 操作间默认延迟
    
    def scale_coordinates(self, x: int, y: int) -> tuple[int, int]:
        """应用缩放因子到坐标"""
        scaled_x = int(x * self.scale_factor)
        scaled_y = int(y * self.scale_factor)
        return (scaled_x, scaled_y)
    
    def click(self, x: int, y: int, button: str = 'left'):
        """
        点击指定坐标
        
        Args:
            x, y: 坐标 (自动应用缩放)
            button: 'left', 'right', 'middle'
        """
        scaled_x, scaled_y = self.scale_coordinates(x, y)
        pyautogui.click(x=scaled_x, y=scaled_y, button=button)
    
    def press(self, key: str, duration: int = 0):
        """
        按键
        
        Args:
            key: 按键名 (如 'space', 'enter', 'a')
            duration: 按住时长 ms (0 表示瞬间)
        """
        if duration > 0:
            pyautogui.keyDown(key)
            time.sleep(duration / 1000.0)
            pyautogui.keyUp(key)
        else:
            pyautogui.press(key)
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """
        移动鼠标
        
        Args:
            x, y: 目标坐标
            duration: 移动时长 (秒)
        """
        scaled_x, scaled_y = self.scale_coordinates(x, y)
        pyautogui.moveTo(scaled_x, scaled_y, duration=duration)
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None):
        """
        滚动滚轮
        
        Args:
            clicks: 滚动量 (正数向上，负数向下)
            x, y: 可选，滚动中心坐标
        """
        if x is not None and y is not None:
            scaled_x, scaled_y = self.scale_coordinates(x, y)
            pyautogui.scroll(clicks, x=scaled_x, y=scaled_y)
        else:
            pyautogui.scroll(clicks)
    
    def delay(self, ms: int):
        """
        延迟
        
        Args:
            ms: 延迟毫秒数
        """
        time.sleep(ms / 1000.0)


class InputRecorder:
    """输入录制器 - 监听输入事件"""
    
    def __init__(self, screen_manager):
        """
        Args:
            screen_manager: ScreenManager 实例
        """
        self.screen_manager = screen_manager
        self.actions: List[RecordedAction] = []
        self.start_time: Optional[float] = None
        self.is_recording = False
        self._mouse_listener = None
        self._keyboard_listener = None
    
    def _get_relative_time(self) -> int:
        """获取相对时间 (ms)"""
        if self.start_time is None:
            return 0
        return int((time.time() - self.start_time) * 1000)
    
    def _on_click(self, x, y, button, pressed):
        """鼠标点击回调"""
        if not self.is_recording or not pressed:
            return
        
        # 获取当前活动窗口
        # 注意：这里需要获取鼠标所在窗口，简化处理
        window_title = "Unknown"
        
        action = RecordedAction(
            timestamp=self._get_relative_time(),
            action_type="mouse_click",
            x=x,
            y=y,
            button=button.name,
            window_title=window_title
        )
        self.actions.append(action)
        print(f"[录制] 鼠标点击：({x}, {y}) {button.name}")
    
    def _on_move(self, x, y):
        """鼠标移动回调 (可选，通常不录制移动)"""
        pass
    
    def _on_key_press(self, key):
        """键盘按下回调"""
        if not self.is_recording:
            return
        
        try:
            key_name = key.char  # 普通字符
        except AttributeError:
            key_name = str(key).replace('Key.', '')  # 特殊键
        
        action = RecordedAction(
            timestamp=self._get_relative_time(),
            action_type="key_press",
            key=key_name
        )
        self.actions.append(action)
        print(f"[录制] 按键：{key_name}")
    
    def start_recording(self):
        """开始录制"""
        self.actions = []
        self.start_time = time.time()
        self.is_recording = True
        
        # 启动监听器
        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        
        self._mouse_listener.start()
        self._keyboard_listener.start()
        print("[录制] 已开始，按 Ctrl+C 停止")
    
    def stop_recording(self) -> List[RecordedAction]:
        """停止录制并返回动作列表"""
        self.is_recording = False
        
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        
        print(f"[录制] 已停止，共录制 {len(self.actions)} 个动作")
        return self.actions
```

**Step 3: 运行测试验证**

```bash
pytest tests/test_input.py -v
```

**Step 4: 提交**

```bash
git add src/core/input.py tests/test_input.py
git commit -m "feat(core): 实现 InputController 输入控制"
```

---

### Task 4: 核心模块 - ImageMatcher

**Files:**
- Create: `src/core/image.py`
- Create: `tests/test_image.py`

**Step 1: 编写测试**

```python
# tests/test_image.py
import pytest
from pathlib import Path
from src.core.image import ImageMatcher, MatchResult


class TestImageMatcher:
    def test_load_template(self, tmp_path):
        """测试加载模板图片"""
        # 创建测试图片
        from PIL import Image
        test_img = Image.new('RGB', (100, 100), color='red')
        template_path = tmp_path / "test.png"
        test_img.save(template_path)
        
        matcher = ImageMatcher()
        template = matcher.load_template(str(template_path))
        assert template is not None
    
    def test_find_template_exact_match(self):
        """测试精确模板匹配"""
        from PIL import Image
        import numpy as np
        
        # 创建屏幕图像 (1000x1000 白色背景)
        screen = Image.new('RGB', (1000, 1000), color='white')
        # 在 (100, 100) 处绘制红色方块 (50x50)
        for x in range(100, 150):
            for y in range(100, 150):
                screen.putpixel((x, y), (255, 0, 0))
        
        # 创建模板 (红色 50x50)
        template = Image.new('RGB', (50, 50), color=(255, 0, 0))
        
        matcher = ImageMatcher()
        result = matcher.find_template(screen, template, confidence=0.9)
        
        assert result is not None
        assert result.confidence >= 0.9
        assert abs(result.x - 100) < 5
        assert abs(result.y - 100) < 5
    
    def test_find_template_no_match(self):
        """测试无匹配情况"""
        from PIL import Image
        
        screen = Image.new('RGB', (1000, 1000), color='white')
        template = Image.new('RGB', (50, 50), color='red')
        
        matcher = ImageMatcher()
        result = matcher.find_template(screen, template, confidence=0.9)
        
        assert result is None
```

**Step 2: 实现 ImageMatcher**

```python
# src/core/image.py
"""图像识别模块 - OpenCV 模板匹配"""
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


@dataclass
class MatchResult:
    """匹配结果"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    @property
    def center(self) -> tuple[int, int]:
        """返回匹配区域中心点"""
        return (self.x + self.width // 2, self.y + self.height // 2)


class ImageMatcher:
    """图像匹配器"""
    
    def __init__(self, default_confidence: float = 0.8):
        """
        Args:
            default_confidence: 默认匹配置信度阈值
        """
        self.default_confidence = default_confidence
        self._template_cache: dict[str, np.ndarray] = {}
    
    def load_template(self, path: str) -> Optional[np.ndarray]:
        """
        加载模板图片
        
        Args:
            path: 图片路径
        
        Returns:
            OpenCV numpy 数组或 None
        """
        # 检查缓存
        if path in self._template_cache:
            return self._template_cache[path]
        
        # 加载图片
        if not Path(path).exists():
            return None
        
        # PIL 转 OpenCV
        pil_img = Image.open(path)
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # 缓存
        self._template_cache[path] = cv_img
        return cv_img
    
    def clear_cache(self):
        """清除模板缓存"""
        self._template_cache.clear()
    
    def find_template(
        self,
        screen: Image.Image,
        template: np.ndarray,
        confidence: Optional[float] = None
    ) -> Optional[MatchResult]:
        """
        在屏幕图像中查找模板
        
        Args:
            screen: 屏幕截图 (PIL Image)
            template: 模板图片 (OpenCV numpy)
            confidence: 置信度阈值
        
        Returns:
            MatchResult 或 None
        """
        if confidence is None:
            confidence = self.default_confidence
        
        # 转屏幕为 OpenCV
        screen_cv = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        
        # 模板匹配
        result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 检查置信度
        if max_val >= confidence:
            h, w = template.shape[:2]
            return MatchResult(
                x=int(max_loc[0]),
                y=int(max_loc[1]),
                width=w,
                height=h,
                confidence=float(max_val)
            )
        
        return None
    
    def find_all_templates(
        self,
        screen: Image.Image,
        template: np.ndarray,
        confidence: Optional[float] = None,
        max_results: int = 10
    ) -> List[MatchResult]:
        """
        查找所有匹配
        
        Args:
            screen: 屏幕截图
            template: 模板图片
            confidence: 置信度阈值
            max_results: 最大返回数
        
        Returns:
            MatchResult 列表
        """
        if confidence is None:
            confidence = self.default_confidence
        
        screen_cv = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
        
        matches = []
        h, w = template.shape[:2]
        
        # 找到所有超过阈值的匹配
        locations = np.where(result >= confidence)
        
        for pt in zip(*locations[::-1]):
            matches.append(MatchResult(
                x=int(pt[0]),
                y=int(pt[1]),
                width=w,
                height=h,
                confidence=float(result[pt[1], pt[0]])
            ))
            
            if len(matches) >= max_results:
                break
        
        # 按置信度排序
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches
    
    def template_exists(
        self,
        screen: Image.Image,
        template: np.ndarray,
        confidence: Optional[float] = None
    ) -> bool:
        """
        检查模板是否存在
        
        Args:
            screen: 屏幕截图
            template: 模板图片
            confidence: 置信度阈值
        
        Returns:
            True/False
        """
        result = self.find_template(screen, template, confidence)
        return result is not None
```

**Step 3: 运行测试验证**

```bash
pytest tests/test_image.py -v
```

**Step 4: 提交**

```bash
git add src/core/image.py tests/test_image.py
git commit -m "feat(core): 实现 ImageMatcher OpenCV 模板匹配"
```

---

### Task 5: 核心模块 - LuaBridge

**Files:**
- Create: `src/core/lua_bridge.py`
- Create: `tests/test_lua_bridge.py`

**Step 1: 编写测试**

```python
# tests/test_lua_bridge.py
import pytest
from unittest.mock import Mock
from src.core.lua_bridge import LuaBridge


class TestLuaBridge:
    def test_lua_state_creation(self):
        """测试 Lua 状态创建"""
        bridge = LuaBridge()
        assert bridge.state is not None
    
    def test_execute_lua_string(self):
        """测试执行 Lua 字符串"""
        bridge = LuaBridge()
        result = bridge.execute_string("return 2 + 2")
        assert result == 4
    
    def test_register_function(self):
        """测试注册 Python 函数到 Lua"""
        bridge = LuaBridge()
        
        def test_func(x):
            return x * 2
        
        bridge.register_function("test_func", test_func)
        result = bridge.execute_string("return test_func(5)")
        assert result == 10
    
    def test_call_lua_function(self):
        """测试调用 Lua 函数"""
        bridge = LuaBridge()
        bridge.execute_string("""
            function add(a, b)
                return a + b
            end
        """)
        result = bridge.call_function("add", 3, 4)
        assert result == 7
```

**Step 2: 实现 LuaBridge**

```python
# src/core/lua_bridge.py
"""Python-Lua 桥接模块"""
import logging
from typing import Any, Callable, Optional
from lupa import LuaRuntime, LuaError


class LuaBridge:
    """Lua 桥接 - 提供 Python 函数给 Lua 调用"""
    
    def __init__(self):
        """初始化 Lua 运行时"""
        self.state = LuaRuntime()
        self._logger = logging.getLogger(__name__)
        self._registered_functions: dict[str, Callable] = {}
    
    def execute_string(self, lua_code: str) -> Any:
        """
        执行 Lua 代码字符串
        
        Args:
            lua_code: Lua 代码
        
        Returns:
            执行结果
        """
        try:
            return self.state.execute(lua_code)
        except LuaError as e:
            self._logger.error(f"Lua 执行错误：{e}")
            raise
    
    def execute_file(self, lua_file: str) -> Any:
        """
        执行 Lua 文件
        
        Args:
            lua_file: 文件路径
        
        Returns:
            执行结果
        """
        with open(lua_file, 'r', encoding='utf-8') as f:
            lua_code = f.read()
        return self.execute_string(lua_code)
    
    def register_function(self, name: str, func: Callable):
        """
        注册 Python 函数到 Lua 全局环境
        
        Args:
            name: Lua 中的函数名
            func: Python 函数
        """
        self.state.globals()[name] = func
        self._registered_functions[name] = func
    
    def register_functions(self, functions: dict[str, Callable]):
        """批量注册函数"""
        for name, func in functions.items():
            self.register_function(name, func)
    
    def call_function(self, func_name: str, *args) -> Any:
        """
        调用 Lua 中已定义的函数
        
        Args:
            func_name: 函数名
            *args: 函数参数
        
        Returns:
            函数返回值
        """
        lua_func = self.state.globals()[func_name]
        if lua_func is None:
            raise ValueError(f"Lua 函数 '{func_name}' 未定义")
        return lua_func(*args)
    
    def get_global(self, name: str) -> Any:
        """获取 Lua 全局变量"""
        return self.state.globals()[name]
    
    def set_global(self, name: str, value: Any):
        """设置 Lua 全局变量"""
        self.state.globals()[name] = value
    
    def reset(self):
        """重置 Lua 状态"""
        self.state = LuaRuntime()
        self._registered_functions.clear()
```

**Step 3: 运行测试验证**

```bash
pytest tests/test_lua_bridge.py -v
```

**Step 4: 提交**

```bash
git add src/core/lua_bridge.py tests/test_lua_bridge.py
git commit -m "feat(core): 实现 LuaBridge Python-Lua 桥接"
```

---

### Task 6: 核心模块 - ConfigManager

**Files:**
- Create: `src/core/config.py`
- Create: `tests/test_config.py`

**Step 1: 编写测试**

```python
# tests/test_config.py
import pytest
import yaml
from pathlib import Path
from src.core.config import ConfigManager, ScriptConfig


class TestScriptConfig:
    def test_default_config(self):
        """测试默认配置"""
        config = ScriptConfig()
        assert config.window_title is None
        assert config.log_level == "INFO"
        assert config.retry_times == 3
    
    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "window_title": "Test Window",
            "log_level": "DEBUG",
            "retry_times": 5
        }
        config = ScriptConfig.from_dict(data)
        assert config.window_title == "Test Window"
        assert config.log_level == "DEBUG"
        assert config.retry_times == 5


class TestConfigManager:
    def test_load_yaml_file(self, tmp_path):
        """测试加载 YAML 文件"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
window_title: "Test"
log_level: "DEBUG"
""")
        manager = ConfigManager()
        config = manager.load_script_config(str(config_file))
        assert config.window_title == "Test"
```

**Step 2: 实现 ConfigManager**

```python
# src/core/config.py
"""配置管理模块"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Any
from pathlib import Path
import yaml


@dataclass
class ScriptMeta:
    """脚本元数据"""
    name: str = ""
    version: str = "1.0"
    description: str = ""
    created_by: str = "manual"  # recorder/manual


@dataclass
class ScriptConfig:
    """脚本配置"""
    window_title: Optional[str] = None
    screen_region: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    scale_factor: Optional[float] = None
    reference_resolution: Tuple[int, int] = field(default=(1920, 1080))
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_console: bool = True
    on_error: str = "stop"  # stop/retry/ignore
    retry_times: int = 3
    default_timeout: int = 5000  # ms
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScriptConfig':
        """从字典创建配置"""
        if data is None:
            return cls()
        
        # 处理 screen_region 元组
        screen_region = data.get('screen_region')
        if isinstance(screen_region, list):
            screen_region = tuple(screen_region)
        
        return cls(
            window_title=data.get('window_title'),
            screen_region=screen_region,
            scale_factor=data.get('scale_factor'),
            reference_resolution=tuple(data.get('reference_resolution', (1920, 1080))),
            log_level=data.get('log_level', 'INFO'),
            log_file=data.get('log_file'),
            log_console=data.get('log_console', True),
            on_error=data.get('on_error', 'stop'),
            retry_times=data.get('retry_times', 3),
            default_timeout=data.get('default_timeout', 5000)
        )


@dataclass
class ScriptAssets:
    """脚本资源"""
    images: dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScriptAssets':
        """从字典创建资源"""
        if data is None:
            return cls()
        return cls(images=data.get('images', {}))


@dataclass
class MacroScript:
    """宏脚本完整结构"""
    meta: ScriptMeta
    config: ScriptConfig
    assets: ScriptAssets
    lua_script: Optional[str] = None
    scripts: dict[str, str] = field(default_factory=dict)  # 子脚本引用
    detection_zones: dict[str, dict] = field(default_factory=dict)
    actions: List[dict] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)  # 原始 YAML 数据
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MacroScript':
        """从 YAML 字典创建"""
        return cls(
            meta=ScriptMeta(**data.get('meta', {})),
            config=ScriptConfig.from_dict(data.get('config', {})),
            assets=ScriptAssets.from_dict(data.get('assets', {})),
            lua_script=data.get('lua_script'),
            scripts=data.get('scripts', {}),
            detection_zones=data.get('detection_zones', {}),
            actions=data.get('actions', []),
            raw_data=data
        )


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    def load_script_config(self, yaml_path: str) -> ScriptConfig:
        """加载脚本配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return ScriptConfig.from_dict(data.get('config', {}))
    
    def load_script(self, yaml_path: str) -> MacroScript:
        """
        加载完整脚本
        
        Args:
            yaml_path: YAML 文件路径
        
        Returns:
            MacroScript 对象
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return MacroScript.from_dict(data)
    
    def save_script(self, script: MacroScript, yaml_path: str):
        """保存脚本到 YAML 文件"""
        # 使用 raw_data 保持格式
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(script.raw_data, f, allow_unicode=True, default_flow_style=False)
    
    def list_scripts(self, scripts_dir: str) -> List[str]:
        """列出所有可用脚本"""
        scripts = []
        scripts_path = Path(scripts_dir)
        
        if not scripts_path.exists():
            return scripts
        
        for yaml_file in scripts_path.glob("*.yaml"):
            scripts.append(yaml_file.name)
        
        return sorted(scripts)
```

**Step 3: 运行测试验证**

```bash
pytest tests/test_config.py -v
```

**Step 4: 提交**

```bash
git add src/core/config.py tests/test_config.py
git commit -m "feat(core): 实现 ConfigManager 配置管理"
```

---

### Task 7: 脚本模块 - Schema 和 Validator

**Files:**
- Create: `src/script/schema.py`
- Create: `src/script/validator.py`
- Create: `tests/test_validator.py`

**Step 1: 实现 Schema 定义**

```python
# src/script/schema.py
"""YAML 脚本 Schema 定义"""
from typing import List, Optional, Any, Literal


# 动作类型定义
ACTION_TYPES = Literal[
    "click",
    "click_image",
    "keypress",
    "type_text",
    "delay",
    "wait_image",
    "wait_image_disappear",
    "move_mouse",
    "scroll",
    "log",
    "run_script",
    "conditional",
    "loop",
    "parallel",
    "sequence"
]


# 条件类型定义
CONDITION_TYPES = Literal[
    "image_exists",
    "image_not_exists",
    "timeout",
    "custom"
]


# Schema 验证规则
SCRIPT_SCHEMA = {
    "meta": {
        "required": True,
        "fields": {
            "name": {"type": str, "required": True},
            "version": {"type": str, "required": False},
            "description": {"type": str, "required": False},
            "created_by": {"type": str, "required": False}
        }
    },
    "config": {
        "required": False,
        "fields": {
            "window_title": {"type": str, "required": False},
            "log_level": {"type": str, "required": False},
            "retry_times": {"type": int, "required": False}
        }
    },
    "assets": {
        "required": False,
        "fields": {
            "images": {"type": dict, "required": False}
        }
    },
    "actions": {
        "required": False,
        "type": list
    },
    "lua_script": {
        "required": False,
        "type": str
    },
    "scripts": {
        "required": False,
        "type": dict
    },
    "detection_zones": {
        "required": False,
        "type": dict
    }
}
```

**Step 2: 实现 Validator**

```python
# src/script/validator.py
"""脚本验证器"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from src.core.config import ConfigManager, MacroScript


class ValidationError(Exception):
    """验证错误"""
    pass


class ScriptValidator:
    """脚本验证器"""
    
    def __init__(self, scripts_dir: str = "scripts"):
        self.scripts_dir = Path(scripts_dir)
        self._logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
    
    def validate_script_file(self, yaml_path: str) -> Tuple[bool, List[str]]:
        """
        验证脚本文件
        
        Args:
            yaml_path: YAML 文件路径
        
        Returns:
            (是否通过，错误列表)
        """
        errors = []
        
        # 检查文件存在
        if not Path(yaml_path).exists():
            errors.append(f"文件不存在：{yaml_path}")
            return (False, errors)
        
        # 加载脚本
        try:
            script = self.config_manager.load_script(yaml_path)
        except Exception as e:
            errors.append(f"YAML 解析失败：{e}")
            return (False, errors)
        
        # 验证 meta
        if not script.meta.name:
            errors.append("缺少必需的 meta.name 字段")
        
        # 验证 Lua 脚本存在
        if script.lua_script:
            lua_path = self.scripts_dir / script.lua_script
            if not lua_path.exists():
                errors.append(f"Lua 脚本不存在：{lua_path}")
        
        # 验证子脚本引用
        for name, sub_script in script.scripts.items():
            sub_path = self.scripts_dir / sub_script
            if not sub_path.exists():
                errors.append(f"子脚本不存在 [{name}]: {sub_path}")
        
        # 验证图片资源
        for name, img_path in script.assets.images.items():
            full_path = Path(img_path)
            if not full_path.is_absolute():
                full_path = Path(yaml_path).parent / full_path
            if not full_path.exists():
                errors.append(f"图片资源不存在 [{name}]: {full_path}")
        
        # 验证检测区域
        for name, zone in script.detection_zones.items():
            if 'image' not in zone:
                errors.append(f"检测区域缺少 image [{name}]")
                continue
            
            img_path = zone['image']
            full_path = Path(img_path)
            if not full_path.is_absolute():
                full_path = Path(yaml_path).parent / full_path
            if not full_path.exists():
                errors.append(f"检测图片不存在 [{name}]: {full_path}")
        
        is_valid = len(errors) == 0
        return (is_valid, errors)
    
    def show_dependency_tree(
        self,
        yaml_path: str,
        indent: int = 0,
        visited: Optional[set] = None
    ) -> str:
        """显示脚本依赖树"""
        if visited is None:
            visited = set()
        
        script = self.config_manager.load_script(yaml_path)
        name = script.meta.name or Path(yaml_path).name
        
        tree = "  " * indent + f"├─ {name}\n"
        
        # 添加子脚本
        for sub_name, sub_path in script.scripts.items():
            full_path = self.scripts_dir / sub_path
            path_str = str(full_path)
            
            if path_str in visited:
                tree += "  " * (indent + 1) + f"├─ {sub_name} (循环引用)\n"
            else:
                visited.add(path_str)
                tree += self.show_dependency_tree(path_str, indent + 1, visited)
        
        # 添加 Lua 脚本
        if script.lua_script:
            tree += "  " * (indent + 1) + f"├─ {script.lua_script} (Lua)\n"
        
        return tree


# CLI 辅助函数
def validate_script_file(yaml_path: str):
    """CLI: 验证脚本"""
    validator = ScriptValidator()
    is_valid, errors = validator.validate_script_file(yaml_path)
    
    if is_valid:
        print(f"✓ 脚本验证通过：{yaml_path}")
    else:
        print(f"✗ 脚本验证失败：{yaml_path}")
        for error in errors:
            print(f"  - {error}")


def show_script_tree(yaml_path: str):
    """CLI: 显示依赖树"""
    validator = ScriptValidator()
    tree = validator.show_dependency_tree(yaml_path)
    print(tree)
```

**Step 3: 编写测试**

```python
# tests/test_validator.py
import pytest
import yaml
from pathlib import Path
from src.script.validator import ScriptValidator, ValidationError


class TestScriptValidator:
    def test_validate_valid_script(self, tmp_path):
        """测试验证有效脚本"""
        # 创建测试脚本
        script_content = {
            "meta": {"name": "Test Script"},
            "config": {"window_title": "Test"},
            "assets": {"images": {}},
            "lua_script": None
        }
        
        script_file = tmp_path / "test.yaml"
        with open(script_file, 'w') as f:
            yaml.dump(script_content, f)
        
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(script_file))
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_missing_meta(self, tmp_path):
        """测试验证缺少 meta"""
        script_content = {
            "config": {"window_title": "Test"}
        }
        
        script_file = tmp_path / "test.yaml"
        with open(script_file, 'w') as f:
            yaml.dump(script_content, f)
        
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(script_file))
        
        assert not is_valid
        assert any("meta.name" in e for e in errors)
    
    def test_validate_missing_subscript(self, tmp_path):
        """测试验证缺少子脚本"""
        script_content = {
            "meta": {"name": "Test"},
            "scripts": {"attack": "attack.yaml"}
        }
        
        script_file = tmp_path / "test.yaml"
        with open(script_file, 'w') as f:
            yaml.dump(script_content, f)
        
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(script_file))
        
        assert not is_valid
        assert any("子脚本不存在" in e for e in errors)
```

**Step 4: 运行测试并提交**

```bash
pytest tests/test_validator.py -v
git add src/script/schema.py src/script/validator.py tests/test_validator.py
git commit -m "feat(script): 实现脚本验证器和 Schema 定义"
```

---

### Task 8: 录制模块 - ScriptRecorder

**Files:**
- Create: `src/recorder/recorder.py`
- Create: `tests/test_recorder.py`

*(由于篇幅限制，后续模块实现省略详细步骤，遵循相同 TDD 模式)*

---

### Task 9: 执行模块 - ScriptExecutor

**Files:**
- Create: `src/executor/executor.py`
- Create: `src/executor/yaml_parser.py`
- Create: `src/executor/runner.py`
- Create: `tests/test_executor.py`

---

### Task 10: 工具模块 - ZoneCaptor

**Files:**
- Create: `src/tools/zone_captor.py`
- Create: `tests/test_zone_captor.py`

---

### Task 11: 日志系统

**Files:**
- Create: `src/core/logger.py`
- Create: `tests/test_logger.py`

---

### Task 12: 集成测试

**Files:**
- Create: `tests/test_integration.py`
- Create: `tests/fixtures/` (测试用脚本和图片)

---

## 测试策略

### 单元测试覆盖
- 所有核心模块 100% 覆盖
- Mock 外部依赖 (pyautogui, OpenCV)
- 使用 pytest fixtures 管理测试资源

### 集成测试
- 端到端脚本执行测试
- 使用虚拟窗口进行测试
- 模拟真实游戏场景

### 手动测试
- 在真实游戏中测试录制功能
- 验证不同分辨率下的缩放
- 测试长时间运行的稳定性

---

## 提交策略

每个 Task 完成后独立提交：
```bash
git add <files>
git commit -m "feat(<module>): <description>"
```

提交信息规范：
- `feat`: 新功能
- `fix`: Bug 修复
- `test`: 测试相关
- `docs`: 文档
- `refactor`: 重构
- `chore`: 构建/工具

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| pyautogui 被游戏检测 | 高 | 提供 Win32 API 备选方案 |
| OpenCV 匹配性能差 | 中 | 限制搜索区域，使用多线程 |
| Lua 嵌入兼容性问题 | 中 | 提供纯 Python 解释器备选 |
| Windows 版本差异 | 低 | 在多个 Windows 版本测试 |

---

## 验收标准

1. ✅ 成功录制简单操作并生成 YAML
2. ✅ 成功执行录制生成的脚本
3. ✅ Lua 编排脚本可调用子脚本
4. ✅ 图像识别准确率 > 90%
5. ✅ 支持 1920x1080 和 1280x720 分辨率
6. ✅ 所有单元测试通过
7. ✅ 代码覆盖率 > 80%
