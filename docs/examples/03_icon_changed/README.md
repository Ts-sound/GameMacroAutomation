# 图标状态变化监测示例

提供两种检测模式，根据场景选择：

## template 模式

使用 pyautogui 模板匹配，适用于**形状差异明显**的图标。

```bash
python -m src.main run docs/examples/03_icon_changed/template_mode.yaml
```

## histogram 模式

使用颜色直方图对比，适用于**形状相同但颜色不同**的图标（如进度条颜色变化）。

```bash
python -m src.main run docs/examples/03_icon_changed/histogram_mode.yaml
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `template_mode.yaml` + `template_mode.py` | template 模式示例 |
| `histogram_mode.yaml` + `histogram_mode.py` | histogram 模式示例 |
| `images/icon_before.png` | 正常态图标 |
| `images/icon_after.png` | 变化后图标 1 |
| `images/icon_after2.png` | 变化后图标 2 |

## API 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `region` | dict | 监测区域，格式 `{"x": (x1, x2), "y": (y1, y2)}`，值为 0.0-1.0 百分比 |
| `normal_template` | str | 正常态图标名称 |
| `changed_template` | str/List[str] | 变化后图标，支持单个或多个 |
| `color_mode` | str | `"template"` 或 `"histogram"`，默认 `"template"` |
| `histogram_threshold` | float | 直方图相似度阈值，仅 `color_mode="histogram"` 时生效，默认 0.7 |
| `interval_ms` | int | 检测间隔（毫秒），默认 2000ms |
| `on_changed` | callable | 回调函数，参数为 `"normal"`、`"changed"` 或 `"none"` |
| `sound` | dict | 声音配置，`{"type": "system"}` 或 `{"type": "file", "file": "alert.wav"}` |
| `timeout` | int | 超时时间（毫秒），默认无限 |

## 返回值

| 返回值 | 说明 |
|--------|------|
| `(True, (x, y))` | icon 已变化，返回变化图标的全屏坐标 |
| `(False, None)` | 超时或未检测到变化 |

## 注意事项

1. **窗口配置**：修改 YAML 中 `config.window_title` 为实际游戏窗口
2. **图片资源**：`images/` 目录下的图片需要替换为实际场景的图标
3. **区域调整**：根据实际监测目标调整 `region` 百分比坐标
4. **颜色敏感场景**：选择 histogram 模式；形状差异明显场景：选择 template 模式