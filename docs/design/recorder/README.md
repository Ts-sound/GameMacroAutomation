# Recorder 模块设计

## Overview

**职责：** 录制用户的鼠标键盘操作，生成 YAML 脚本和截图资源
- 监听输入事件（鼠标点击、键盘按键）
- 点击时自动截图保存
- 生成可执行的 YAML 脚本

**非职责：** 脚本执行、图像识别

## Architecture

```mermaid
graph TD
    subgraph Recorder["ScriptRecorder"]
        R1[find_game_window]
        R2[start_recording]
        R3[_on_click_capture]
        R4[actions_to_yaml]
        R5[save_script]
    end

    subgraph InputRecorder
        IR1[start_listening]
        IR2[on_click callback]
        IR3[on_key callback]
        IR4[stop_listening]
    end

    subgraph ScreenManager
        SM1[find_window]
        SM2[get_screen_region]
    end

    R1 --> SM1
    R2 --> IR1
    IR1 --> IR2
    IR2 --> R3
    R3 --> SM2
    R3 --> R4
    R4 --> R5

    classDef recorder fill:#87CEEB
    classDef listener fill:#90EE90
    classDef screen fill:#DDA0DD
    class R1,R2,R3,R4,R5 recorder
    class IR1,IR2,IR3,IR4 listener
    class SM1,SM2 screen
```

## Interfaces

| Class | Public Methods | Description |
|-------|---------------|-------------|
| `ScriptRecorder` | record, start_recording, stop_recording, save_script | 录制器主模块 |
| `InputRecorder` | start_listening, stop_listening, actions | 输入事件监听 |

## Key Sequences

### 录制流程

```mermaid
sequenceDiagram
    participant USER as User
    participant REC as ScriptRecorder
    participant IR as InputRecorder
    participant SM as ScreenManager

    USER->>REC: record("Game Window", "test")
    REC->>SM: find_window("Game Window")
    SM-->>REC: WindowInfo
    REC->>IR: start_recording()
    
    Note over IR: Listening for events...
    
    USER->>GAME: Click in game
    GAME->>IR: mouse_click(x, y)
    IR->>REC: on_click(x, y, button)
    REC->>SM: get_screen_region(window, x, y)
    SM-->>REC: screenshot
    REC-->>REC: save to images/click_001.png
    
    USER->>IR: Press F12 to stop
    IR->>REC: stop_recording()
    REC->>REC: actions_to_yaml()
    REC-->>REC: save test.yaml
    REC-->>USER: Script saved
```

### 点击截图流程

```mermaid
sequenceDiagram
    participant IR as InputRecorder
    participant REC as ScriptRecorder
    participant SM as ScreenManager

    IR->>REC: on_click(x, y, button)
    
    rect rgb(240,248,255)
        Note over REC: Calculate region
        REC->>SM: find_window(title)
        SM-->>REC: current_window
        REC->>REC: rel_x = x - window.left
        REC->>REC: rel_y = y - window.top
    end
    
    REC->>SM: get_screen_region(window, rel_x, rel_y, size, size)
    SM-->>REC: screenshot
    
    REC-->>REC: save images/click_NNN.png
    REC-->>IR: screenshot saved
```

## Error Handling

| Error Type | Handling |
|------------|----------|
| Window not found | Show list of available windows |
| Screenshot failed | Fallback to screen coordinates |
| YAML save failed | Raise exception with path |

## Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit | actions_to_yaml, save_script |
| Mock | ScreenManager, InputRecorder |
| Integration | Full recording flow |

## YAML Output Format

```yaml
meta:
  name: "Recording"
  version: "1.0"
  created_by: "recorder"

config:
  window_title: "Game Window"
  log_level: "INFO"

assets:
  images:
    click_001: "images/click_001.png"

actions:
  - type: "click_image"
    image: "click_001"
    offset: [1339, 1548]
  - type: "delay"
    ms: 200
  - type: "keypress"
    key: "a"
```

## Future Improvements

- [ ] Add pause/resume recording
- [ ] Support editing actions after recording
- [ ] Add preview before saving