# Executor 模块设计

## Overview

**职责：** 执行 Python 脚本，提供图像识别、输入控制、循环控制等 API
- 加载并执行 YAML + Python 混合脚本
- 为 Python 脚本提供自动化 API
- 错误处理与重试机制

**非职责：** 录制功能、脚本验证

## Architecture

```mermaid
graph TD
    subgraph Executor["ScriptExecutor"]
        E1[load_script]
        E2[validate_script]
        E3[setup_window]
        E4[execute]
    end

    subgraph Runner["PythonRunner"]
        R1[load_script]
        R2[execute_module]
    end

    subgraph API["ScriptAPI"]
        A1[click_image]
        A2[image_exists]
        A3[wait_image]
        A4[loop_while]
        A5[loop_times]
        A6[loop_until]
        A7[run_script]
    end

    E1 --> E2
    E2 --> E3
    E3 --> E4
    E4 --> R1
    R1 --> R2
    R2 --> A1
    R2 --> A2
    R2 --> A3
    R2 --> A4
    R2 --> A5
    R2 --> A6
    R2 --> A7

    classDef executor fill:#87CEEB
    classDef runner fill:#90EE90
    classDef api fill:#DDA0DD
    class E1,E2,E3,E4 executor
    class R1,R2 runner
    class A1,A2,A3,A4,A5,A6,A7 api
```

## Interfaces

| Class | Public Methods | Description |
|-------|---------------|-------------|
| `ScriptExecutor` | execute, setup_logging, setup_window | 执行器主模块 |
| `PythonRunner` | load_script, execute | Python 脚本加载执行 |
| `ScriptAPI` | click_image, wait_image, loop_while, etc. | 脚本 API 封装 |

## Key Sequences

### Python 脚本执行流程

```mermaid
sequenceDiagram
    participant USER as User
    participant CLI as CLI
    participant EXE as ScriptExecutor
    participant RUN as PythonRunner
    participant API as ScriptAPI
    participant CORE as Core Layer

    USER->>CLI: run script.yaml
    CLI->>EXE: execute(script.yaml)
    EXE->>EXE: load_script(yaml)
    EXE->>EXE: validate_script()
    EXE->>EXE: setup_window(title)
    EXE->>EXE: setup_scale_factor()
    EXE->>RUN: load_script(python_script.py)
    RUN->>RUN: import module
    RUN->>API: main(executor)
    
    loop Script execution
        API->>CORE: click_image("btn")
        CORE-->>API: result
        API->>CORE: image_exists("hp")
        CORE-->>API: exists
        alt condition true
            API->>CORE: click_image("attack")
        end
    end
    
    API-->>RUN: return True/False
    RUN-->>EXE: success/failed
    EXE-->>CLI: result
    CLI-->>USER: Done
```

### 循环控制流程

```mermaid
sequenceDiagram
    participant SCRIPT as Python Script
    participant API as ScriptAPI
    participant EXE as Executor

    SCRIPT->>API: loop_while(condition, body, 100, 1000)
    
    loop max_iterations=100
        API->>EXE: call condition()
        EXE-->>API: True/False
        
        alt condition is True
            API->>EXE: call body()
            EXE-->>API: result
            API->>API: delay(1000)
        else condition is False
            API-->>SCRIPT: loop completed
            break
        end
    end
```

## Error Handling

| Strategy | Behavior |
|----------|----------|
| `stop` | 立即停止执行（默认） |
| `retry` | 重试 retry_times 次后停止 |
| `ignore` | 忽略错误继续执行 |

```yaml
config:
  on_error: "stop"    # stop / retry / ignore
  retry_times: 3
  default_timeout: 5000
```

## Testing Strategy

| Test Type | Coverage |
|-----------|----------|
| Unit | execute, load_script, validate_script |
| Integration | Full script execution with mocked core |
| Mock | ScreenManager, ImageMatcher, InputController |

## Future Improvements

- [ ] Add async execution support
- [ ] Support cancellation during execution
- [ ] Add execution profiling/tracing