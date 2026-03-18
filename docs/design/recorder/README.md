# Recorder 模块设计

## 概述

Recorder 模块负责录制用户的鼠标键盘操作，生成 YAML 脚本和截图资源。

## 模块结构

```
src/recorder/
├── __init__.py
└── recorder.py          # 录制器主模块
```

## 组件设计

### ScriptRecorder (recorder.py)

**职责：** 录制输入、截图、生成 YAML 脚本

**类设计：**
```python
class ScriptRecorder:
    __init__(output_dir="scripts", screenshot_size=400)
    
    # 窗口管理
    find_game_window(title: str) -> Optional[WindowInfo]
    
    # 录制控制
    start_recording(window_title: str) -> bool
    stop_recording() -> List[RecordedAction]
    
    # 截图
    capture_click_region(x, y) -> Optional[str]
    _capture_screen_region(x, y) -> Optional[str]
    
    # YAML 生成
    actions_to_yaml(actions, window_title, image_map) -> dict
    save_script(yaml_data, script_name) -> str
    
    # 完整录制流程
    record(window_title, output_name) -> str
    
    # 回调
    _on_click_capture(x, y, button) -> Optional[str]
    _on_stop_recording()

# CLI 辅助函数
list_windows()
record_script(output, window, screenshot_size)
```

**属性：**
```python
output_dir: Path           # 输出目录
images_dir: Path           # 图片保存目录
screen_manager: ScreenManager
input_recorder: Optional[InputRecorder]
current_window: Optional[WindowInfo]
screenshot_size: int       # 截图区域大小（默认 400）
click_counter: int         # 点击计数器
image_map: dict            # 动作索引 -> 截图文件名
```

## 录制流程

```
1. 启动录制工具
   ↓
2. 选择/定位游戏窗口 (find_game_window)
   ↓
3. 开始录制 (start_recording)
   - 创建 InputRecorder
   - 注册点击回调 (_on_click_capture)
   - 注册 F12 停止回调
   ↓
4. 用户执行操作
   - 鼠标点击 → 触发回调 → 截图保存
   - 键盘按下 → 记录按键
   ↓
5. 按 F12 或 Ctrl+C 停止
   ↓
6. 生成 YAML (actions_to_yaml)
   ↓
7. 保存脚本 (save_script)
```

## 截图策略

### 点击时实时截图

```python
def _on_click_capture(self, x, y, button):
    """点击回调 - 实时截图"""
    img_file = self.capture_click_region(x, y)
    if img_file:
        action_idx = len(self.input_recorder.actions)
        self.image_map[action_idx] = img_file
    return img_file
```

### 截图区域计算

```python
def capture_click_region(self, x, y):
    # 重新获取窗口位置（窗口可能被移动）
    current_window = self.screen_manager.find_window(window_title)
    
    # 计算相对窗口坐标
    rel_x = x - current_window.left
    rel_y = y - current_window.top
    
    # 检查坐标是否在窗口内
    if 超出窗口范围:
        return self._capture_screen_region(x, y)  # fallback 到屏幕截图
    
    # 计算截图区域（以点击点为中心）
    half_size = self.screenshot_size // 2
    x1 = max(0, rel_x - half_size)
    y1 = max(0, rel_y - half_size)
    
    # 截图并保存
    screenshot = self.screen_manager.get_screen_region(...)
    filename = f"click_{self.click_counter:03d}.png"
    screenshot.save(self.images_dir / filename)
```

## YAML 生成

### 输出格式

```yaml
meta:
  name: "录制脚本"
  version: "1.0"
  created_by: "recorder"

config:
  window_title: "游戏窗口"
  log_level: "INFO"
  retry_times: 3

assets:
  images:
    click_001: "images/click_001.png"
    click_002: "images/click_002.png"

actions:
  - type: "click_image"
    image: "click_001"
    offset: [1339, 1548]  # 屏幕坐标，用于 fallback
  
  - type: "delay"
    ms: 200
  
  - type: "keypress"
    key: "a"
```

### 动作类型映射

| 录制动作 | YAML 类型 | 说明 |
|---------|---------|------|
| mouse_click | click_image | 优先使用图像识别，offset 作为 fallback |
| key_press | keypress | 键盘按键 |
| - | delay | 动作间的时间间隔 |

## CLI 命令

### 录制脚本

```bash
python -m src.main record -o scripts/test.yaml -w "游戏窗口" -s 400
```

**参数：**
- `-o, --output`: 输出 YAML 文件路径
- `-w, --window`: 游戏窗口标题
- `-s, --screenshot-size`: 截图区域大小（默认 400）

### 列出窗口

```bash
python -m src.main record -o scripts/test.yaml
# 不指定 -w 时自动列出可用窗口
```

## 依赖关系

```
ScriptRecorder
├── ScreenManager (screen.py)
├── InputRecorder (input.py)
└── ConfigManager (config.py) - 用于 YAML 生成
```

## 使用示例

### 基本录制

```python
from src.recorder.recorder import ScriptRecorder

recorder = ScriptRecorder(output_dir="scripts", screenshot_size=400)
script_path = recorder.record("游戏窗口", "test")
print(f"脚本已保存：{script_path}")
```

### 使用 CLI

```bash
# 1. 列出窗口
python -m src.main record -o scripts/test.yaml

# 2. 指定窗口录制
python -m src.main record -o scripts/test.yaml -w "Notepad++"

# 3. 自定义截图大小
python -m src.main record -o scripts/test.yaml -w "游戏窗口" -s 600
```

## 注意事项

### 截图大小选择

| 大小 | 适用场景 |
|------|---------|
| 100-200 | 小按钮、精确匹配 |
| 300-400 | 普通 UI 元素（默认） |
| 500-800 | 大区域、复杂 UI |

### 录制技巧

1. **保持窗口位置固定** - 窗口移动可能导致截图位置偏差
2. **点击 UI 元素的固定区域** - 避开动画部分
3. **动作间隔清晰** - 便于生成合理的 delay

## 测试

```python
# tests/test_recorder.py
class TestScriptRecorder:
    def test_init(self, tmp_path)
    def test_generate_script_name(self, tmp_path)
    def test_actions_to_yaml_basic(self, tmp_path)
    def test_actions_to_yaml_with_delay(self, tmp_path)
    def test_save_script(self, tmp_path)
```
