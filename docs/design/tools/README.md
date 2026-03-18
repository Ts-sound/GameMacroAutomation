# Tools 模块设计

## 概述

Tools 模块提供辅助工具，主要是检测区域截图功能。

## 模块结构

```
src/tools/
├── __init__.py
└── zone_captor.py     # 检测区域截图工具
```

## 组件设计

### ZoneCaptor (zone_captor.py)

**职责：** 截取检测区域图片

**类设计：**
```python
class ZoneCaptor:
    __init__()
    
    find_window(title: str) -> Optional[WindowInfo]
    capture_full_screen(output_path: str) -> str
    capture_window(window: WindowInfo, output_path: str) -> str
    capture_region(window, x, y, w, h, output_path) -> str
    interactive_capture(window_title, output_dir) -> str

# CLI 辅助函数
capture_zone(output, window)
```

**依赖：**
- `ScreenManager` - 窗口管理
- `PIL.ImageGrab` - 屏幕截图

## 截图方式

### 1. 全屏截图

```python
captor = ZoneCaptor()
captor.capture_full_screen("assets/detection/full.png")
```

### 2. 窗口截图

```python
window = captor.find_window("游戏窗口")
if window:
    captor.capture_window(window, "assets/detection/window.png")
```

### 3. 区域截图

```python
# 相对窗口坐标
captor.capture_region(
    window=window,
    x=100, y=50, w=200, h=30,
    output_path="assets/detection/boss_hp.png"
)

# 全屏坐标（window=None）
captor.capture_region(
    window=None,
    x=500, y=300, w=100, h=100,
    output_path="assets/detection/region.png"
)
```

### 4. 交互式截图（简化版）

由于跨平台 GUI 限制，当前实现提供使用说明：

```python
captor.interactive_capture("游戏窗口", "assets/detection/")
```

输出说明：
```
============================================================
检测区域截图工具
============================================================

由于当前环境限制，请使用以下方式截图:

1. Windows 自带截图工具 (Win + Shift + S)
2. 或使用截图软件截取游戏窗口区域
3. 保存截图到指定目录

建议保存位置：assets/detection/
```

## CLI 命令

### 截图检测区域

```bash
# 截取全屏
python -m src.main capture-zone --output assets/detection/full.png

# 截取指定窗口
python -m src.main capture-zone --output assets/detection/window.png -w "游戏窗口"

# 不指定窗口时提示
python -m src.main capture-zone --output assets/detection/xxx.png
```

## 依赖关系

```
ZoneCaptor
└── ScreenManager (core/screen.py)
```

## 使用场景

### 1. 定义检测区域

在 YAML 脚本中定义检测区域：

```yaml
detection_zones:
  boss_hp_bar:
    image: "detection/boss_hp.png"
    confidence: 0.85
    region: [100, 50, 200, 30]
    description: "Boss 血条存在检测"
```

### 2. 录制时自动截图

录制器会在每次点击时自动截图，保存到 `scripts/images/` 目录。

## 替代方案

### Windows 平台

```python
# 使用 PIL.ImageGrab 直接截图
from PIL import ImageGrab

# 全屏
screenshot = ImageGrab.grab()

# 区域
region = ImageGrab.grab(bbox=(x1, y1, x2, y2))
```

### 使用外部工具

| 工具 | 命令 | 平台 |
|------|------|------|
| Windows 截图 | Win + Shift + S | Windows |
| Snipping Tool | `snippingtool` | Windows |
| Flameshot | `flameshot gui` | Linux |
| Screencapture | `screencapture -i` | macOS |

## 测试

```python
# tests/test_zone_captor.py
class TestZoneCaptor:
    def test_capture_full_screen(self, tmp_path)
    def test_capture_window(self, tmp_path)
    def test_capture_region(self, tmp_path)
```

## 注意事项

### 截图尺寸建议

| 用途 | 推荐尺寸 | 说明 |
|------|---------|------|
| 按钮/图标 | 50x50 - 100x100 | 精确匹配 |
| 血条/状态 | 200x30 - 300x50 | 长条形区域 |
| 弹窗/对话框 | 200x200 - 400x300 | 较大区域 |

### 截图质量

1. **避免动态元素** - 不要截取动画、闪烁的部分
2. **选择特征明显区域** - 颜色、形状独特的部分
3. **留出适当边界** - 不要紧贴边缘

### 文件命名

```
assets/detection/
├── boss_hp.png          # Boss 血条
├── low_hp_warning.png   # 低血量警告
├── reward_popup.png     # 奖励弹窗
└── start_btn.png        # 开始按钮
```
