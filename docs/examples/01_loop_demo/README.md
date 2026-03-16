# 循环控制示例

演示如何使用 `loop_while` 进行条件循环。

## 运行方式

```bash
python -m src.main run docs/examples/01_loop_demo/main.yaml
```

## 功能演示

- 使用 `wait_image()` 等待目标图片出现
- 使用 `loop_while()` 进行条件循环
- 使用 `run_script()` 调用子脚本
- 图片资源管理（录制生成的图片）

## 文件说明

| 文件 | 说明 |
|------|------|
| `main.py` | Python 主脚本，包含循环逻辑 |
| `main.yaml` | YAML 配置文件 |
| `test.yaml` | 子脚本示例 |
| `images/` | 录制的图片资源目录 |

## 核心代码

```python
def main(executor):
    # 等待目标出现
    if not executor.wait_image("screen_001", 10000):
        executor.log("目标未出现，退出", "ERROR")
        return False
    
    # 条件循环
    executor.loop_while(
        lambda: executor.image_exists("screen_001"),
        lambda: executor.run_script("test.yaml"),
        max_iterations=3
    )
    return True
```

## 配置说明

```yaml
config:
  window_title: "Notepad++"  # 目标窗口
  log_level: "INFO"

assets:
  images:
    screen_001: images/screen_001.png  # 相对路径引用

python_script: "main.py"
```

## 注意事项

1. **窗口配置**: 默认配置为 "Notepad++"，使用前请修改为实际游戏窗口
2. **图片资源**: `images/` 目录下的图片是录制生成的，需要根据实际情况重新录制
3. **循环次数**: 示例中 `max_iterations=3`，可根据需要调整
