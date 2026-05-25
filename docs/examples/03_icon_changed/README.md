# 图标状态变化监测示例

演示如何使用 `monitor_icon_state` 监测图标状态变化并发出提示音。

## 运行方式

```bash
python -m src.main run docs/examples/03_icon_changed/main.yaml
```

## 功能演示

- 使用 `monitor_icon_state()` 监测图标状态变化
- 区域指定使用百分比格式（相对于屏幕）
- 状态变化后发出系统提示音
- 支持自定义回调函数

## 文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | Python 主脚本，包含监测逻辑 |
| `main.yaml` | YAML 配置文件 |
| `images/` | 图标图片资源（需根据实际场景替换） |

## 核心代码

```python
def main(executor):
    # 定义监测区域（百分比格式）
    region = {
        "x": (0.4, 0.6),  # 40%-60% 屏幕宽度
        "y": (0.1, 0.2)   # 10%-20% 屏幕高度
    }

    # 回调函数：状态变化时调用
    def on_state_changed(new_state: str):
        executor.log(f"图标状态变化: {new_state}", "WARNING")

    # 监测图标状态变化
    # 返回: (bool, tuple) -> (是否检测到变化, 全屏坐标)
    changed, coords = executor.monitor_icon_state(
        region=region,
        normal_template="icon_before",
        changed_template="icon_after",
        interval_ms=2000,
        on_changed=on_state_changed,
        sound={"type": "system"},
        timeout=60000
    )

    if changed and coords:
        x, y = coords
        executor.log(f"检测到图标状态变化，位置: ({x}, {y})", "INFO")
    return True
```

## 配置说明

```yaml
config:
  window_title: "Notepad++"
  log_level: "INFO"

assets:
  images:
    icon_before: "images/icon_before.png"  # 正常态图标
    icon_after: "images/icon_after.png"    # 变化后图标

python_script: "main.py"
```

## API 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `region` | dict | 监测区域，格式 `{"x": (x1, x2), "y": (y1, y2)}`，值为 0.0-1.0 百分比 |
| `normal_template` | str | 正常态图标名称 |
| `changed_template` | str | 变化后图标名称 |
| `interval_ms` | int | 检测间隔（毫秒），默认 2000ms |
| `on_changed` | callable | 回调函数，参数为 `"normal"`、`"changed"` 或 `"none"` |
| `sound` | dict | 声音配置，`{"type": "system"}` 或 `{"type": "file", "file": "alert.wav"}` |
| `timeout` | int | 超时时间（毫秒），默认无限 |

## 返回值

| 返回值 | 说明 |
|--------|------|
| `(True, (x, y))` | icon 已变化，返回变化图标的**全屏坐标** |
| `(False, None)` | 超时或未检测到变化 |

## 注意事项

1. **窗口配置**: 默认配置为 "Notepad++"，使用前请修改为实际游戏窗口
2. **图片资源**: `images/` 目录下的图片需要替换为实际场景的图标
3. **区域调整**: 根据实际监测目标调整 `region` 百分比坐标
4. **声音配置**: 支持系统提示音或自定义音频文件