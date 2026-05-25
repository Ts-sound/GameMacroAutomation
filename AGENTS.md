# 项目规范

## 技术栈

- **语言：** Python 3.10+
- **目标平台：** Windows only（依赖 pyautogui、pynput、pygetwindow）
- **构建工具：** setuptools + pyproject.toml

## 目录结构

```
src/
├── core/           # 核心模块（screen, input, image, config, logger）
├── recorder/       # 录制器模块
├── executor/       # 执行器模块（executor, api）
├── script/         # 脚本验证模块（validator, schema）
└── tools/          # 辅助工具模块（zone_captor）

scripts/            # 用户脚本目录（含 .yaml + .py 配对文件）
assets/
├── templates/      # 动作模板图片
└── detection/      # 检测区域图片
tests/              # 测试目录
logs/               # 日志输出
```

## 编码规范

- **代码格式化：** black
- **代码检查：** ruff
- **类型检查：** mypy
- **测试框架：** pytest
- **行长度：** 88 字符（pyproject.toml）

## 命令

```bash
# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 测试
pytest

# 格式化 + 检查
black src/ tests/
ruff check src/ tests/

# CLI 命令
python -m src.main record -o scripts/test.yaml -s 400    # 录制
python -m src.main run scripts/test.yaml                 # 运行
python -m src.main validate scripts/test.yaml            # 验证
python -m src.main capture-zone -o assets/detection/x.png  # 截图区域
python -m src.main list                                  # 列出脚本
python -m src.main tree scripts/entry.yaml               # 依赖树
```

## 脚本架构

- **YAML：** 元数据、配置、资源引用、检测区域定义
- **Python：** 流程控制，脚本文件需定义 `main(executor)` 函数

```yaml
# scripts/attack.yaml
meta:
  name: "攻击"
  version: "1.0"
config:
  window_title: "游戏窗口"
assets:
  images:
    attack_btn: "attack.png"
python_script: "attack.py"
```

```python
# scripts/attack.py
def main(executor):
    executor.click_image("attack_btn")
    executor.delay(200)
    return True
```

## API（executor 提供）

| 方法 | 用途 |
|------|------|
| `click_image(name, confidence=0.8)` | 点击图片 |
| `image_exists(name)` | 检查图片存在 |
| `wait_image(name, timeout=5000)` | 等待图片 |
| `run_script(name)` | 运行子脚本 |
| `delay(ms)` | 延迟 |
| `log(msg, level)` | 日志 |
| `loop_while(condition, body, max_iterations, interval)` | 条件循环 |
| `loop_times(count, body, delay_ms)` | 固定次数循环 |
| `loop_until(condition, body, timeout)` | 直到满足条件 |

## 已知问题

- **main.py bug:** `list` 和 `tree` 命令导入不存在的 `src.script.manager`，实际函数在 `src.core.config` 和 `src.script.validator`

## 设计文档

- 使用 mermaid 图表
- 模块文档：Overview, Architecture, Interfaces, Error Handling
- 总体设计：[docs/design/README.md](docs/design/README.md)