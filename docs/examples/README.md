# 示例项目

本目录包含完整的游戏宏自动化示例。

## 目录结构

```
examples/
├── README.md                 # 本文件
├── basic_combat/            # 基础战斗循环示例
│   ├── main.py              # Python 脚本入口
│   ├── main.yaml            # YAML 配置文件
│   ├── test.yaml            # 子脚本示例
│   └── images/              # 图片资源目录
│       ├── screen_001.png
│       └── ...
└── battle_loop/             # 高级战斗循环示例
    ├── battle_loop.py       # Python 脚本
    └── battle_loop.yaml     # YAML 配置
```

## 示例列表

### 1. basic_combat - 基础战斗循环

**功能演示：**
- 使用 `wait_image()` 等待目标出现
- 使用 `loop_while()` 进行条件循环
- 使用 `run_script()` 调用子脚本
- 图片资源管理（录制生成的图片）

**运行方式：**
```bash
python -m src.main run docs/examples/basic_combat/main.yaml
```

**文件说明：**
| 文件 | 说明 |
|------|------|
| `main.py` | Python 主脚本，包含循环逻辑 |
| `main.yaml` | YAML 配置，定义窗口、图片资源等 |
| `test.yaml` | 子脚本示例，演示脚本调用 |
| `images/` | 录制生成的图片资源 |

**核心代码：**
```python
def main(executor):
    # 等待目标出现
    if not executor.wait_image("screen_001", 10000):
        return False
    
    # 条件循环
    executor.loop_while(
        lambda: executor.image_exists("screen_001"),
        lambda: executor.run_script("test.yaml"),
        max_iterations=3
    )
```

### 2. battle_loop - 高级战斗循环

**功能演示：**
- 多阶段战斗流程
- 使用 `loop_times()` 固定次数循环
- 使用 `loop_until()` 直到条件满足
- 条件判断和分支逻辑

**运行方式：**
```bash
python -m src.main run docs/examples/battle_loop.yaml
```

**文件说明：**
| 文件 | 说明 |
|------|------|
| `battle_loop.py` | 完整的战斗流程脚本 |
| `battle_loop.yaml` | YAML 配置 |

## 运行所有示例

```bash
# 1. 基础战斗循环
python -m src.main run docs/examples/basic_combat/main.yaml

# 2. 高级战斗循环
python -m src.main run docs/examples/battle_loop.yaml
```

## 创建自己的脚本

1. **录制基础动作**
   ```bash
   python -m src.main record --output scripts/my_script.yaml
   ```

2. **创建 Python 脚本**
   ```python
   # scripts/my_flow.py
   def main(executor):
       executor.log("开始执行", "INFO")
       executor.click_image("attack_btn")
       return True
   ```

3. **创建 YAML 配置**
   ```yaml
   # scripts/my_flow.yaml
   meta:
     name: "我的脚本"
   
   config:
     window_title: "游戏窗口"
   
   assets:
     images:
       attack_btn: "assets/templates/attack_btn.png"
   
   python_script: "my_flow.py"
   ```

4. **运行脚本**
   ```bash
   python -m src.main run scripts/my_flow.yaml
   ```

## 更多信息

- [Python 脚本使用指南](../python_script_guide.md) - 详细 API 文档
- [设计文档](../design/README.md) - 系统架构说明
- [主 README](../README.md) - 项目总览
