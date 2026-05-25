# 图标状态变化监测示例

提供三种检测模式，根据场景选择：

## color 模式（推荐）

使用去背景模板 + alpha 通道提取真实颜色，无需 icon_after 模板。

```bash
python -m src.main run docs/examples/03_icon_changed/color_mode.yaml
```

**原理**：
1. 用去背景模板 `icon_before_nobg.png` 定位 icon 位置
2. 用模板 alpha 通道作为 mask，提取截图对应区域的真实颜色
3. 首次检测记录初始颜色，后续对比颜色差异
4. 差异 > `color_diff_threshold` → changed

**优势**：不需要 `icon_after`，只检测图标本身颜色变化

## template 模式

使用 pyautogui 模板匹配，适用于**形状差异明显**的图标。

```bash
python -m src.main run docs/examples/03_icon_changed/template_mode.yaml
```

## histogram 模式

使用颜色直方图对比，适用于**形状相同但颜色不同**的图标。

```bash
python -m src.main run docs/examples/03_icon_changed/histogram_mode.yaml
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `color_mode.yaml` + `color_mode.py` | color 模式（推荐） |
| `template_mode.yaml` + `template_mode.py` | template 模式 |
| `histogram_mode.yaml` + `histogram_mode.py` | histogram 模式 |
| `images/icon_before_nobg.png` | 去背景模板（推荐使用） |

## API 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `region` | dict | 监测区域，格式 `{"x": (x1, x2), "y": (y1, y2)}` |
| `normal_template` | str | 正常态模板名（推荐使用 `_nobg.png` 去背景模板） |
| `changed_template` | str/List[str] | 变化后图标，color 模式不需要 |
| `color_mode` | str | `"template"` / `"histogram"` / `"color"` |
| `color_diff_threshold` | float | color 模式颜色差异阈值，默认 0.15 |
| `histogram_threshold` | float | histogram 模式阈值，默认 0.7 |
| `interval_ms` | int | 检测间隔，默认 2000ms |
| `on_changed` | callable | 回调函数 |
| `sound` | dict | 声音配置 |

## 返回值

| 返回值 | 说明 |
|--------|------|
| `(True, (x, y))` | icon 已变化 |
| `(False, None)` | 超时或未检测到变化 |