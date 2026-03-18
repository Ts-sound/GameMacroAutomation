# Executor 模块设计

## 概述

Executor 模块负责执行 Python 脚本和 YAML 动作序列，提供图像识别、输入控制、脚本调用等功能。

## 模块结构

```
src/executor/
├── __init__.py
├── executor.py        # 执行器主模块
└── api.py             # Python 脚本 API
```

## 组件设计

### 1. ScriptExecutor (executor.py)

**职责：** 加载和执行脚本

**类设计：**
```python
class ScriptExecutor:
    __init__(scripts_dir="scripts", assets_dir="assets")
    
    # 日志和配置
    setup_logging(log_level, log_file)
    load_script(yaml_path) -> MacroScript
    validate_script(yaml_path) -> Tuple[bool, List[str]]
    
    # 窗口设置
    setup_window(window_title) -> bool
    setup_scale_factor(reference_resolution)
    setup_script_api()
    
    # 执行
    execute(yaml_path) -> bool
    _execute_python_script(python_script) -> bool
    _execute_actions(actions, on_error) -> bool
    
    # 图像识别（供 ScriptAPI 调用）
    _click_image(name, confidence, offset)
    _image_exists(name, confidence) -> bool
    _wait_image(name, timeout, confidence) -> bool
    
    # 脚本调用（供 ScriptAPI 调用）
    _run_sub_script(script_name) -> bool
```

**属性：**
```python
scripts_dir: Path
assets_dir: Path
config_manager: ConfigManager
validator: ScriptValidator
screen_manager: ScreenManager
image_matcher: ImageMatcher
input_controller: Optional[InputController]
python_runner: Optional[PythonRunner]
script_api: Optional[ScriptAPI]
_logger: Optional[logging.Logger]
current_window: Optional[WindowInfo]
scale_factor: float
current_script_dir: Optional[Path]
```

### 2. PythonRunner (api.py)

**职责：** 加载和执行 Python 脚本

**类设计：**
```python
class PythonRunner:
    __init__(script_executor)
    
    load_script(script_path) -> Optional[ModuleType]
    execute(module) -> bool
```

### 3. ScriptAPI (api.py)

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
    loop_count: int
```

## 执行流程

### YAML 脚本执行

```
1. 加载 YAML (load_script)
   ↓
2. 验证脚本 (validate_script)
   ↓
3. 设置窗口 (setup_window)
   ↓
4. 设置缩放因子 (setup_scale_factor)
   ↓
5. 判断脚本类型
   ├─ 有 python_script → _execute_python_script
   └─ 有 actions → _execute_actions
   ↓
6. 输出鼠标统计
   ↓
7. 返回执行结果
```

### Python 脚本执行

```
1. 加载 Python 模块 (PythonRunner.load_script)
   ↓
2. 调用 main(executor) 函数
   ↓
3. 处理返回值
   ├─ True → 成功
   ├─ False → 失败
   └─ Exception → 捕获并记录错误
```

## Python 脚本 API 详解

### 图像识别

```python
# 点击图片（图像识别定位）
executor.click_image("attack_btn", confidence=0.8)

# 检查图片是否存在
if executor.image_exists("boss_hp_bar"):
    executor.log("Boss 出现了！", "INFO")

# 等待图片出现
if executor.wait_image("start_btn", timeout=10000):
    executor.click_image("start_btn")
else:
    executor.log("等待超时", "ERROR")
```

### 脚本控制

```python
# 运行子脚本
executor.run_script("potion.yaml")

# 延迟
executor.delay(1000)  # 1 秒

# 日志
executor.log("开始战斗", "INFO")
executor.log("血量低", "WARNING")
```

### 循环控制

```python
# loop_while - 条件循环
executor.loop_while(
    condition=lambda: executor.image_exists("boss_hp_bar"),
    body=lambda: executor.click_image("attack_btn") or executor.delay(1000),
    max_iterations=100,
    interval=1000
)

# loop_times - 固定次数循环
executor.loop_times(
    count=5,
    body=lambda: executor.click_image("item_1") or executor.delay(300),
    delay_ms=200
)

# loop_until - 直到条件满足
executor.loop_until(
    condition=lambda: executor.image_exists("reward_popup"),
    body=lambda: executor.click_image("collect_btn") or executor.delay(1000),
    timeout=30000,
    interval=2000
)
```

## 图像识别策略

### 优先级

1. **pyautogui.locateCenterOnScreen** - 直接在屏幕上查找
2. **offset fallback** - 使用录制时存储的屏幕坐标

### 坐标处理

```python
def _click_image(self, name, confidence, offset):
    # 1. 尝试图像识别
    location = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
    
    if location:
        # 图像识别成功，直接点击（不应用缩放）
        x, y = location
        self.input_controller.click_with_move(x, y, apply_scale=False)
        return
    
    # 2. 图像识别失败，使用 offset 作为 fallback
    if offset and len(offset) == 2:
        screen_x, screen_y = int(offset[0]), int(offset[1])
        scaled_x = int(screen_x * self.scale_factor)
        scaled_y = int(screen_y * self.scale_factor)
        self.input_controller.click_with_move(scaled_x, scaled_y)
```

## 错误处理

### on_error 策略

```yaml
config:
  on_error: "stop"  # stop/retry/ignore
  retry_times: 3
```

| 策略 | 行为 |
|------|------|
| `stop` | 立即停止执行 |
| `retry` | 重试，最多 retry_times 次 |
| `ignore` | 忽略错误继续执行 |

### 异常处理

```python
def _execute_actions(self, actions, on_error):
    for i, action in enumerate(actions):
        try:
            # 执行动作
            ...
        except Exception as e:
            self.log(f"动作 {i+1} 执行失败：{e}", "ERROR")
            if on_error == "stop":
                return False
    return True
```

## 日志系统

### 日志等级

```python
executor.log("详细参数", "DEBUG")
executor.log("动作执行", "INFO")
executor.log("匹配度偏低", "WARNING")
executor.log("图片未找到", "ERROR")
```

### 执行报告

```python
# 执行结束后自动生成
executor._logger.save_report("logs/report.yaml")
```

## 依赖关系

```
ScriptExecutor
├── ConfigManager (config.py)
├── ScriptValidator (script/validator.py)
├── ScreenManager (core/screen.py)
├── ImageMatcher (core/image.py)
├── InputController (core/input.py)
├── PythonRunner (api.py)
└── ScriptAPI (api.py)
```

## 使用示例

### 执行 YAML 脚本

```python
from src.executor.executor import ScriptExecutor

executor = ScriptExecutor()
executor.setup_logging(log_level="INFO")
success = executor.execute("scripts/attack.yaml")
```

### 执行 Python 脚本

```yaml
# scripts/my_script.yaml
meta:
  name: "我的脚本"

config:
  window_title: "游戏窗口"

assets:
  images:
    attack_btn: "assets/attack_btn.png"

python_script: "my_script.py"
```

```python
# scripts/my_script.py
def main(executor):
    executor.log("开始执行", "INFO")
    
    if not executor.wait_image("attack_btn", 5000):
        return False
    
    executor.click_image("attack_btn")
    executor.delay(1000)
    
    return True
```

### CLI 使用

```bash
# 执行脚本
python -m src.main run scripts/my_script.yaml

# 指定窗口（覆盖脚本配置）
python -m src.main run scripts/my_script.yaml -w "其他窗口"

# 指定日志等级
python -m src.main run scripts/my_script.yaml -l DEBUG
```

## 测试

```python
# tests/test_executor.py
class TestScriptExecutor:
    def test_execute_python_script(self, tmp_path)
    def test_execute_actions(self, tmp_path)
    def test_image_recognition(self, tmp_path)
    def test_loop_while(self, tmp_path)
    def test_loop_times(self, tmp_path)
    def test_loop_until(self, tmp_path)
```

## 注意事项

### 图像识别

1. **置信度选择**
   - 0.8-0.9: 精确匹配（推荐）
   - 0.5-0.7: 模糊匹配（动态 UI）

2. **坐标缩放**
   - 图像识别返回的坐标是屏幕实际坐标，不应用缩放
   - offset 存储的是录制时的屏幕坐标，需要应用缩放

### 循环控制

1. **始终设置 max_iterations/timeout** - 防止死循环
2. **合理设置 interval** - 给游戏反应时间（建议≥500ms）
3. **循环体内调用 delay** - 避免过快执行
