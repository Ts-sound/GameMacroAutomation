# Tools 模块设计

## Overview

**职责：** 辅助工具集
- 检测区域截图
- 交互式截图（说明模式）

**非职责：** 脚本执行、录制、验证

## Architecture

```mermaid
graph TD
    subgraph ZoneCaptor["ZoneCaptor"]
        Z1[find_window]
        Z2[capture_full_screen]
        Z3[capture_window]
        Z4[capture_region]
        Z5[interactive_capture]
    end

    subgraph ScreenManager
        SM1[find_window]
        SM2[get_screen_region]
    end

    Z1 --> SM1
    Z2 --> SM2
    Z3 --> SM1
    Z3 --> SM2
    Z4 --> SM1
    Z4 --> SM2
    Z5 --> Z1

    classDef tools fill:#87CEEB
    classDef screen fill:#90EE90
    class Z1,Z2,Z3,Z4,Z5 tools
    class SM1,SM2 screen
```

## Interfaces

| Class | Public Methods | Description |
|-------|---------------|-------------|
| `ZoneCaptor` | capture_full_screen, capture_window, capture_region, interactive_capture | 截图工具 |

## Key Sequences

### 区域截图流程

```mermaid
sequenceDiagram
    participant USER as User
    participant ZC as ZoneCaptor
    participant SM as ScreenManager

    USER->>ZC: capture_region(window, x, y, w, h, output)
    ZC->>SM: find_window(title)
    SM-->>ZC: WindowInfo
    ZC->>SM: get_screen_region(window, x, y, w, h)
    SM-->>ZC: screenshot
    ZC-->>ZC: save to output_path
    ZC-->>USER: output_path
```

## Screenshot Methods

| Method | Use Case |
|--------|----------|
| `capture_full_screen` | 完整屏幕截图 |
| `capture_window` | 整个游戏窗口 |
| `capture_region` | 指定区域（相对窗口或全屏坐标） |
| `interactive_capture` | 显示交互式截图说明 |

## CLI Usage

```bash
# 全屏截图
python -m src.main capture-zone --output assets/detection/full.png

# 指定窗口
python -m src.main capture-zone --output assets/detection/window.png -w "Game Window"

# 不指定窗口时列出可用窗口
python -m src.main capture-zone --output assets/detection/xxx.png
```

## Screenshot Size Guide

| Usage | Recommended Size |
|-------|-----------------|
| Button/Icon | 50x50 - 100x100 |
| HP Bar/Status | 200x30 - 300x50 |
| Popup/Dialog | 200x200 - 400x300 |

## Error Handling

| Error Type | Handling |
|------------|----------|
| Window not found | Show available windows |
| Screenshot failed | Raise exception with details |
| Output path invalid | Show path validation error |

## Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit | capture_region with mocked PIL |
| Integration | Real screenshot operations |

## Future Improvements

- [ ] Add cross-platform screenshot support
- [ ] Add interactive region selection GUI
- [ ] Add screenshot preview before saving