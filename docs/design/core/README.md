# Core 模块设计

## Overview

**职责：** 提供游戏宏自动化的底层能力
- 窗口管理与截图
- 鼠标键盘模拟与监听
- 图像识别（模板匹配）
- YAML 配置加载
- 日志记录与执行报告

**非职责：** 脚本执行逻辑、录制流程控制

## Architecture

```mermaid
graph TD
    subgraph External["External"]
        GAME[Game Window]
    end

    subgraph ScreenManager
        SM1[find_window]
        SM2[get_screen_region]
        SM3[auto_detect_scale_factor]
    end

    subgraph InputController
        IC1[click_with_move]
        IC2[press]
        IC3[delay]
    end

    subgraph ImageMatcher
        IM1[locateCenterOnScreen]
        IM2[load_template]
    end

    subgraph ConfigManager
        CM1[load_script]
        CM2[save_script]
    end

    subgraph MacroLogger
        LOG1[info/error/warning]
        LOG2[save_report]
    end

    GAME --> SM1
    SM1 --> SM2
    SM2 --> IM1
    IM1 --> IC1
    IC1 --> GAME

    CM1 --> SM1
    LOG1 --> CM1

    classDef module fill:#87CEEB
    classDef api fill:#90EE90
    class SM1,SM2,SM3,IC1,IC2,IC3,IM1,IM2,CM1,CM2,LOG1,LOG2 api
```

## Interfaces

| Class | Public Methods | Description |
|-------|---------------|-------------|
| `WindowInfo` | title, left, top, width, height | 窗口信息数据类 |
| `ScreenManager` | find_window, get_screen_region, auto_detect_scale_factor | 窗口与截图管理 |
| `InputController` | click_with_move, press, delay, get_stats | 输入控制 |
| `ImageMatcher` | locate_center_on_screen, load_template | 图像识别 |
| `ConfigManager` | load_script, save_script | YAML 配置管理 |
| `MacroLogger` | info, error, start_execution, save_report | 日志系统 |

## Key Sequences

### 执行脚本流程

```mermaid
sequenceDiagram
    participant EXE as Executor
    participant SM as ScreenManager
    participant IM as ImageMatcher
    participant IC as InputController

    EXE->>SM: find_window("Game")
    SM-->>EXE: WindowInfo
    EXE->>IM: locateCenterOnScreen("btn.png")
    IM-->>EXE: (x, y) or None
    alt Image found
        EXE->>IC: click_with_move(x, y)
        IC-->>EXE: done
    else Image not found
        EXE-->>EXE: use offset fallback
    end
```

### 录制流程

```mermaid
sequenceDiagram
    participant REC as Recorder
    participant IR as InputRecorder
    participant SM as ScreenManager

    REC->>SM: find_window(title)
    SM-->>REC: WindowInfo
    REC->>IR: start_recording()
    Note over IR: Listen mouse/keyboard events
    IR->>REC: on_click(x, y, button)
    REC->>SM: get_screen_region(x, y)
    REC-->>IR: screenshot saved
    IR->>REC: on_stop()
    REC->>REC: actions_to_yaml()
    REC-->>REC: YAML saved
```

## Error Handling

| Error Type | Handling |
|------------|----------|
| Window not found | Raise `WindowNotFoundError` |
| Screenshot failed | Fallback to full screen |
| Image not found | Log warning, return None |
| YAML parse error | Raise `YAMLError` with details |

## Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit | ScreenManager.find_window, InputController.click |
| Mock | pyautogui, PIL.ImageGrab |
| Integration | Screen + Image recognition |

## Future Improvements

- [ ] Add cross-platform screen capture (currently Windows only)
- [ ] Support multiple monitor configurations
- [ ] Optimize image matching performance with caching