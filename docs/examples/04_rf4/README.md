
## 需求

## 脚本流程

1. 检测 01_ready.png ，Y -> 点击 `;`
2. 检测 02_on_fish.png , Y -> 长按 `;`
3. 检测 03_keep.png , Y -> 点击 `空格`
4. 循环 -> 1
5. 检测 04_move_in_bottom.png , Y -> 长按 `;`
6. 循环 -> 1

图片检测设置，指定区域位置（中心位置，可配置），区域大小为400x400(可配置)，grayscale=True ， 置信度

## 运行

```bash
python -m src.main run docs/examples/04_rf4/rf4.yaml
```

## 检测设置（rf4.yaml detection_zones）

| 字段 | 说明 | 默认 |
|------|------|------|
| `center` | 区域中心位置（绝对像素，可配置） | `[960, 540]` |
| `size` | 区域尺寸（可配置） | `[400, 400]` |
| `grayscale` | 灰度匹配 | `true` |
| `confidence` | 置信度 | `0.8` |

每个区域名即模板名，对应 `images/<区域名>.png`。

## 键盘控制

协议参考说明：/opt/tong/ws/git-repo/esp32-python-keyboard/README.md
连接到 指定ip端口 (如：192.168.137.11 80)
目前只发送单键及组合键
其他控制后续在添加

### ESP32 键盘模块

- **模块**: [esp32_keyboard.py](esp32_keyboard.py)（纯标准库，无第三方依赖）
- **示例**: [esp_keyboard_demo.py](esp_keyboard_demo.py)

**连接**: TCP 持久连接，自动重连。默认 `192.168.137.11:80`，可在 `esp32_keyboard.py`
顶部 `DEFAULT_HOST` / `DEFAULT_PORT` 修改。

**API**:

| 方法 | 说明 |
|------|------|
| `tap(key, press_ms=50)` | 单击（press -> sleep -> release） |
| `hold(key, duration_ms)` | 长按（press -> sleep -> release） |
| `combo(keys, press_ms=50)` | 组合键，如 `["ctrl", "s"]` |
| `press(key)` / `release(key)` | 原始按下/释放 |
| `release_all()` | 释放全部按键 |
| `connect()` / `close()` | 连接管理 |

**用法**:

```python
from esp32_keyboard import Esp32Keyboard

kb = Esp32Keyboard()           # 默认 192.168.137.11:80
kb.connect()
kb.tap(";", press_ms=50)       # 单击 ;
kb.hold(";", duration_ms=500)  # 长按 ;
kb.combo(["ctrl", "s"])        # 组合键
kb.close()
```

**通信约定**（与 ESP32 端 wifi_service/keyboard_service 匹配）:

- 每个命令一条 JSON，`{"v":1,"type":"keyboard","action":"<action>","params":{...}}`
- 每次命令后读取 ESP32 的完整 JSON 响应，校验 `success` 字段
- ESP32 仅接受单客户端；命令逐条发送，不并行



