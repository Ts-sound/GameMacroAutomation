# Design Documents

## Overview

**项目定位：** 基于 Python 的 Windows 游戏宏自动化系统
**核心价值：** 录制鼠标键盘操作 → 生成脚本 → 通过图像识别自动执行

## Architecture

```mermaid
graph TD
    subgraph CLI["CLI Layer"]
        CLI1[record]
        CLI2[run]
        CLI3[validate]
        CLI4[capture-zone]
        CLI5[list]
        CLI6[tree]
    end

    subgraph Module["Functional Modules"]
        REC[Recorder]
        EXE[Executor]
        VAL[Validator]
        ZC[ZoneCaptor]
    end

    subgraph Core["Core Layer"]
        SM[ScreenManager]
        IC[InputController]
        IM[ImageMatcher]
        CM[ConfigManager]
        LOG[Logger]
        SA[ScriptAPI]
        DD[Detector]
        SN[SoundNotifier]
    end

    CLI1 --> REC
    CLI2 --> EXE
    CLI3 --> VAL
    CLI4 --> ZC

    REC --> SM
    REC --> IC
    EXE --> SA
    EXE --> IM
    EXE --> CM
    EXE --> LOG
    EXE --> DD
    EXE --> SN

    SA --> SM
    SA --> IC
    SA --> IM
    SA --> DD
    SA --> SN
    DD --> SM
    DD --> IM
    SN --> SM

    classDef cli fill:#90EE90
    classDef module fill:#87CEEB
    classDef core fill:#DDA0DD
    class CLI1,CLI2,CLI3,CLI4,CLI5,CLI6 cli
    class REC,EXE,VAL,ZC module
    class SM,IC,IM,CM,LOG,SA,DD,SN core
```

## Modules

| Module | Responsibility | Documentation |
|--------|---------------|---------------|
| core | Screen, input, image, config, logging | [core/](core/README.md) |
| core/detector | Region-based template detection | - |
| core/sound | Sound notification (system/file) | - |
| recorder | Record mouse/keyboard → YAML | [recorder/](recorder/README.md) |
| executor | Execute Python scripts with API | [executor/](executor/README.md) |
| script | YAML validation and management | [script/](script/README.md) |
| tools | Zone capture utility | [tools/](tools/README.md) |

## Data Model

```mermaid
classDiagram
    class MacroScript {
        +ScriptMeta meta
        +ScriptConfig config
        +ScriptAssets assets
        +str python_script
        +Dict scripts
        +List actions
    }

    class ScriptMeta {
        +str name
        +str version
        +str description
        +str created_by
    }

    class ScriptConfig {
        +str window_title
        +int screenshot_size
        +float scale_factor
        +str log_level
        +str on_error
        +int retry_times
    }

    class ScriptAssets {
        +Dict images
    }

    MacroScript --> ScriptMeta
    MacroScript --> ScriptConfig
    MacroScript --> ScriptAssets
```

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Script format | YAML + Python | Human-readable + powerful logic |
| Image recognition | pyautogui | Mature, simple API |
| Input control | pyautogui + pynput | Stable, cross-platform |
| Window management | PyGetWindow | Simple window lookup |
| Resolution adaptation | Auto-scale factor | Support multiple resolutions |

## API Design

### Script API (executor provides)

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `click_image` | name, confidence=0.8 | void | Click matched image |
| `image_exists` | name, confidence=0.8 | bool | Check image exists |
| `wait_image` | name, timeout=5000 | bool | Wait for image |
| `run_script` | name | bool | Run sub-script |
| `delay` | ms | void | Delay in milliseconds |
| `log` | message, level | void | Log message |
| `loop_while` | condition, body, max_iter, interval | void | Loop while condition true |
| `loop_times` | count, body, delay_ms | void | Loop fixed times |
| `loop_until` | condition, body, timeout, interval | void | Loop until condition true |
| `detect_in_region` | region, template_name, confidence | List[MatchResult] | Detect templates in percentage region |
| `monitor_icon_state` | region, normal, changed, interval, on_changed | bool | Monitor state change with callback |

### Region Detection

#### Region Format (Percentage-based)

```python
region = {
    "x": (0.0, 0.5),  # Left-closed, right-open interval: 0% to 50% of screen width
    "y": (0.0, 1.0)   # 0% to 100% of screen height
}
```

- **Coordinate system**: Screen absolute coordinates
- **Reference**: Current screen (primary) or specified by screen_id
- **Left (x=0)** to **Right (x=1)**, **Top (y=0)** to **Bottom (y=1)**

#### detect_in_region

Detect all occurrences of a template within a percentage-defined screen region.

```python
results = executor.detect_in_region(
    region={"x": (0.4, 0.6), "y": (0.1, 0.2)},  # Percentage region
    template_name="boss_icon",                   # Template name in assets
    confidence=0.8                               # Optional, default 0.8
) -> List[MatchResult]
```

#### monitor_icon_state

Continuously monitor an icon's state change. Play sound and trigger callback when state changes.

```python
# Monitor state change with callback
def on_state_change(new_state: str):  # "normal", "changed", or "none"
    executor.log(f"State changed to: {new_state}")

changed, coords = executor.monitor_icon_state(
    region={"x": (0.4, 0.6), "y": (0.1, 0.2)},
    normal_template="boss_hp_normal",
    changed_template="boss_hp_low",
    interval_ms=2000,
    on_changed=on_state_change,
    sound={"type": "system"},  # or {"type": "file", "file": "alert.wav"}
    timeout=60000              # Optional, default no timeout
)

# Returns: (bool, tuple) -> (changed, (screen_x, screen_y))
# (True, (960, 540)) - icon changed, return full-screen coordinates
# (False, None) - timeout or no change detected
```

**Detection cycle returns:**
- `"none"`: No icon detected
- `"normal"`: Original icon detected
- `"changed"`: Icon has changed

#### MatchResult

```python
@dataclass
class MatchResult:
    x: int          # Center X relative to region (0 = left edge of region)
    y: int          # Center Y relative to region
    width: int      # Match width
    height: int     # Match height
    confidence: float
    screen_x: int   # Absolute screen coordinate X
    screen_y: int   # Absolute screen coordinate Y
```

### Terminology

| Term | Format | Example |
|------|--------|---------|
| Region | `{"x": (float, float), "y": (float, float)}` | `{"x": (0.0, 0.5), "y": (0.0, 1.0)}` |
| Percentage | Float 0.0-1.0 | 0.5 = 50% |
| Sound config | `{"type": "system" \| "file", "file": str}` | `{"type": "file", "file": "alert.wav"}` |
| State | String "normal" \| "changed" | `"normal"` |

## Script Architecture

```mermaid
graph LR
    subgraph YAML["YAML Layer (Data)"]
        Y1[meta]
        Y2[config]
        Y3[assets]
        Y4[detection_zones]
    end

    subgraph Python["Python Layer (Logic)"]
        P1[main function]
        P2[loop_while]
        P3[loop_until]
        P4[conditionals]
    end

    Y1 --> P1
    Y2 --> P1
    Y3 --> P1
    Y4 --> P1
    P1 --> P2
    P1 --> P3
    P1 --> P4
```

```yaml
# YAML: metadata, config, assets
meta:
  name: "Battle Flow"
config:
  window_title: "Game"
assets:
  images:
    attack_btn: "assets/attack_btn.png"
python_script: "battle.py"
```

## Security Considerations

- **Local execution only** - All automation runs locally, no remote access
- **Window isolation** - Operations scoped to specific game window
- **No external network calls** - Pure local desktop automation
- **Credential handling** - No credentials stored; game credentials entered by user directly
- **Input simulation safety** - Mouse/keyboard simulation limited to recorded actions

## Deployment

```mermaid
graph LR
    subgraph User["User Environment"]
        USER[User]
        GAME[Game Window]
    end

    subgraph Application["Game Macro Automation"]
        CLI[CLI Interface]
        EXE[Executor]
        CORE[Core Modules]
    end

    USER --> CLI
    CLI --> EXE
    EXE --> CORE
    CORE --> GAME

    classDef user fill:#90EE90
    classDef app fill:#87CEEB
    classDef target fill:#DDA0DD
    class USER,GAME user
    class CLI,EXE,CORE app
    class GAME target
```

### Installation

```bash
# Clone and install
git clone <repo>
cd GameMacroAutomation
pip install -r requirements.txt

# Run CLI
python -m src.main --help
```

### Configuration

- Script directory: `scripts/`
- Assets directory: `assets/`
- Logs directory: `logs/`
- Config: YAML files in scripts directory