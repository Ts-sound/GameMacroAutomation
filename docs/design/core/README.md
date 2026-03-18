# Core 模块设计

## 概述

Core 模块提供游戏宏自动化的核心功能，包括屏幕捕捉、输入控制、图像识别、配置管理和 Python 脚本 API。

## 模块结构

```
src/core/
├── __init__.py
├── screen.py          # 屏幕/窗口管理
├── input.py           # 输入控制
├── image.py           # 图像识别
├── config.py          # 配置管理
└── logger.py          # 日志系统
```

## 组件设计

### 1. ScreenManager (screen.py)

**职责：** 屏幕捕捉、游戏窗口定位、分辨率适配

**类设计：**
```python
class WindowInfo:
    """窗口信息数据类"""
    title: str
    left: int
    top: int
    width: int
    height: int
    right: int  # 计算属性
    bottom: int # 计算属性

class ScreenManager:
    find_window(title: str) -> Optional[WindowInfo]
    get_window_size(window: WindowInfo) -> Tuple[int, int]
    get_screen_size() -> Tuple[int, int]
    calculate_scale_factor(current, reference) -> float
    get_screen_region(window, x, y, w, h) -> Image
    auto_detect_scale_factor(window_title, reference_resolution) -> Optional[float]
```

**依赖：**
- `pygetwindow` - 窗口管理
- `PIL.ImageGrab` - 屏幕截图
- `screeninfo` - 屏幕信息（可选）

**使用示例：**
```python
from src.core.screen import ScreenManager

screen = ScreenManager()
window = screen.find_window("游戏窗口")
if window:
    scale = screen.auto_detect_scale_factor("游戏窗口", (1920, 1080))
    screenshot = screen.get_screen_region(window, 0, 0, 100, 100)
```

---

### 2. InputController (input.py)

**职责：** 监听和模拟鼠标键盘输入

**类设计：**
```python
class RecordedAction:
    """录制的动作"""
    timestamp: int       # 相对时间 ms
    action_type: str     # mouse_click, key_press
    x: Optional[int]
    y: Optional[int]
    button: Optional[str]
    key: Optional[str]

class MouseStats:
    """鼠标移动统计"""
    total_distance: float
    total_duration: float
    move_count: int
    avg_speed: float         # pixels/ms
    avg_speed_pixels_per_second: float

class InputController:
    __init__(scale_factor=1.0, logger=None)
    click(x, y, button)
    click_with_move(x, y, button, apply_scale=True)  # 带移动轨迹的点击
    press(key, duration)
    move_mouse(x, y, duration)
    scroll(clicks, x, y)
    delay(ms)
    get_stats() -> MouseStats
    reset_stats()

class InputRecorder:
    __init__(screen_manager, on_click_callback, on_stop_callback, stop_key)
    start_recording()
    stop_recording() -> List[RecordedAction]
```

**依赖：**
- `pyautogui` - 鼠标键盘模拟
- `pynput` - 输入监听

**使用示例：**
```python
from src.core.input import InputController

controller = InputController(scale_factor=1.0)
controller.click_with_move(100, 200)  # 移动到 (100,200) 后点击
controller.press('space')
controller.delay(1000)

# 获取统计
stats = controller.get_stats()
print(f"平均速度：{stats.avg_speed_pixels_per_second:.0f} px/s")
```

---

### 3. ImageMatcher (image.py)

**职责：** 图像识别、模板匹配

**类设计：**
```python
class MatchResult:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    center: Tuple[int, int]  # 计算属性

class ImageMatcher:
    __init__(default_confidence=0.8)
    load_template(path: str) -> Optional[Image]
    clear_cache()
    find_template(screen, template, confidence) -> Optional[MatchResult]
    find_all_templates(screen, template, confidence, max_results) -> List[MatchResult]
    template_exists(screen, template, confidence) -> bool
    locate_on_screen(template_path, confidence) -> Optional[Tuple]
    locate_center_on_screen(template_path, confidence) -> Optional[Tuple]
```

**依赖：**
- `pyautogui` - 图像识别
- `PIL` - 图像处理

**使用示例：**
```python
from src.core.image import ImageMatcher

matcher = ImageMatcher(default_confidence=0.8)
template = matcher.load_template("assets/attack_btn.png")

# 方法 1: 使用 pyautogui 直接识别
location = pyautogui.locateCenterOnScreen("assets/attack_btn.png", confidence=0.8)

# 方法 2: 使用 ImageMatcher
result = matcher.find_template(screen, template)
if result:
    print(f"找到图片，中心点：{result.center}")
```

---

### 4. ConfigManager (config.py)

**职责：** YAML 脚本的加载、保存、验证

**数据类设计：**
```python
@dataclass
class ScriptMeta:
    name: str
    version: str
    description: str
    created_by: str  # recorder/manual

@dataclass
class ScriptConfig:
    window_title: Optional[str]
    screen_region: Optional[Tuple[int, int, int, int]]
    scale_factor: Optional[float]
    reference_resolution: Tuple[int, int] = (1920, 1080)
    log_level: str = "INFO"
    log_file: Optional[str]
    log_console: bool = True
    on_error: str = "stop"  # stop/retry/ignore
    retry_times: int = 3
    default_timeout: int = 5000

@dataclass
class ScriptAssets:
    images: Dict[str, str] = field(default_factory=dict)

@dataclass
class MacroScript:
    meta: ScriptMeta
    config: ScriptConfig
    assets: ScriptAssets
    python_script: Optional[str] = None
    scripts: Dict[str, str] = field(default_factory=dict)
    detection_zones: Dict[str, dict] = field(default_factory=dict)
    actions: List[dict] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)

class ConfigManager:
    load_script_config(yaml_path) -> ScriptConfig
    load_script(yaml_path) -> MacroScript
    save_script(script, yaml_path)
    list_scripts(scripts_dir) -> List[str]
```

**依赖：**
- `pyyaml` - YAML 解析
- `pydantic` - 数据验证（可选）

**使用示例：**
```python
from src.core.config import ConfigManager

config_manager = ConfigManager()
script = config_manager.load_script("scripts/attack.yaml")
print(f"脚本名称：{script.meta.name}")
print(f"窗口：{script.config.window_title}")
```

---

### 5. Logger (logger.py)

**职责：** 日志记录、执行报告生成

**类设计：**
```python
@dataclass
class ExecutionReport:
    script: str
    start_time: str
    end_time: str
    duration_seconds: float
    status: str  # running/success/failed/stopped
    steps_total: int
    steps_completed: int
    errors: List[str]
    warnings: List[str]
    python_logs: List[str]
    
    to_dict() -> dict
    to_yaml() -> str

class MacroLogger:
    __init__(name, log_level, log_file, log_console)
    debug(msg)
    info(msg)
    warning(msg)
    error(msg)
    start_execution(script_path)
    end_execution(status)
    step_start(step_name)
    step_complete()
    save_report(output_path)
    get_report() -> Optional[ExecutionReport]

class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
```

**依赖：**
- `logging` - Python 标准日志
- `pyyaml` - 执行报告输出

**使用示例：**
```python
from src.core.logger import MacroLogger

logger = MacroLogger("gma", log_level="INFO", log_file="logs/run.log")
logger.start_execution("scripts/attack.yaml")
logger.info("开始执行")
logger.step_start("进入战斗")
# ... 执行动作
logger.step_complete()
logger.end_execution("success")
logger.save_report("logs/report.yaml")
```

---

### 6. ScriptAPI (api.py)

**职责：** 为 Python 脚本提供 API 封装

**类设计：**
```python
class ScriptAPI:
    __init__(script_executor)
    
    # 图像识别 API
    click_image(name, confidence)
    image_exists(name, confidence) -> bool
    wait_image(name, timeout) -> bool
    
    # 脚本控制 API
    run_script(name) -> bool
    delay(ms)
    log(message, level)
    
    # 循环控制 API
    loop_while(condition, body, max_iterations, interval)
    loop_times(count, body, delay_ms)
    loop_until(condition, body, timeout, interval)
    
    # 状态
    loop_count: int  # 当前循环计数
```

**依赖：**
- `ScriptExecutor` - 脚本执行器

**使用示例：**
```python
# scripts/my_script.py
def main(executor):
    executor.log("开始执行", "INFO")
    
    if not executor.wait_image("boss_hp_bar", 10000):
        return False
    
    executor.loop_while(
        lambda: executor.image_exists("boss_hp_bar"),
        lambda: executor.click_image("attack_btn") or executor.delay(1000),
        max_iterations=100
    )
    
    return True
```

---

## 模块间依赖关系

```
ScreenManager ← InputController
ScreenManager ← ImageMatcher
ScreenManager ← ScriptAPI
InputController ← ScriptAPI
ImageMatcher ← ScriptAPI
ConfigManager ← ScriptExecutor
Logger ← ScriptExecutor
ScriptAPI → ScriptExecutor
```

## 测试策略

### 单元测试
- 每个公开方法至少一个测试
- Mock 外部依赖（pyautogui, PIL）

### 集成测试
- ScreenManager + ImageMatcher 联合测试
- ScriptAPI 完整流程测试

### 测试文件
- `tests/test_screen.py`
- `tests/test_input.py`
- `tests/test_image.py`
- `tests/test_config.py`
- `tests/test_logger.py`
- `tests/test_api.py`
