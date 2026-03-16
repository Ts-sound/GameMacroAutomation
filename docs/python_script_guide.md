# Python 脚本使用指南

## 概述

游戏宏自动化系统支持使用 Python 编写复杂的流程控制脚本。通过 Python，你可以使用完整的编程语言特性来实现复杂的逻辑。

## 快速开始

### 1. 创建 Python 脚本

```python
# my_script.py
def main(executor):
    executor.log("开始执行", "INFO")
    
    # 点击按钮
    executor.click_image("attack_btn")
    
    # 延迟
    executor.delay(1000)
    
    return True
```

### 2. 创建 YAML 配置

```yaml
# my_script.yaml
meta:
  name: "我的脚本"
  version: "1.0"

config:
  window_title: "游戏窗口"
  log_level: "INFO"

assets:
  images:
    attack_btn: "assets/templates/attack_btn.png"

python_script: "my_script.py"
```

### 3. 运行脚本

```bash
python -m src.main run my_script.yaml
```

## ScriptAPI 参考

### 图像识别

#### `click_image(name, confidence=0.8)`
点击图片。

```python
executor.click_image("attack_btn")
executor.click_image("skill_btn", confidence=0.9)
```

#### `image_exists(name, confidence=0.8) -> bool`
检查图片是否存在。

```python
if executor.image_exists("boss_hp_bar"):
    executor.log("Boss 出现了！", "INFO")
```

#### `wait_image(name, timeout=5000) -> bool`
等待图片出现，超时返回 False。

```python
if executor.wait_image("start_btn", 10000):
    executor.click_image("start_btn")
else:
    executor.log("等待超时", "ERROR")
```

### 脚本控制

#### `run_script(name) -> bool`
运行子脚本。

```python
executor.run_script("potion.yaml")
```

#### `delay(ms)`
延迟指定毫秒。

```python
executor.delay(1000)  # 延迟 1 秒
```

#### `log(message, level="INFO")`
记录日志。

```python
executor.log("开始战斗", "INFO")
executor.log("血量低", "WARNING")
executor.log("出现错误", "ERROR")
```

### 循环控制

#### `loop_while(condition, body, max_iterations=100, interval=1000)`
当条件为 true 时持续循环。

```python
executor.loop_while(
    lambda: executor.image_exists("boss_hp_bar"),
    lambda: executor.click_image("attack_btn") or executor.delay(1000),
    max_iterations=100,
    interval=1000
)
```

#### `loop_times(count, body, delay_ms=0)`
固定次数循环。

```python
executor.loop_times(
    5,
    lambda: executor.click_image("item_1") or executor.delay(300),
    delay_ms=200
)
```

#### `loop_until(condition, body, timeout=30000, interval=1000)`
直到条件满足才停止。

```python
executor.loop_until(
    lambda: executor.image_exists("reward_popup"),
    lambda: executor.click_image("collect_btn") or executor.delay(1000),
    timeout=30000,
    interval=2000
)
```

## 完整示例

### 战斗流程

```python
def main(executor):
    executor.log("=== 战斗开始 ===", "INFO")
    
    # 等待 Boss 出现
    if not executor.wait_image("boss_hp_bar", 10000):
        executor.log("Boss 未出现", "ERROR")
        return False
    
    # 战斗循环
    executor.loop_while(
        lambda: executor.image_exists("boss_hp_bar"),
        lambda: (
            executor.run_script("potion.yaml") 
            if executor.image_exists("low_hp_warning")
            else executor.click_image("attack_btn")
        ) or executor.delay(1000),
        max_iterations=100
    )
    
    # 拾取物品
    executor.loop_times(
        5,
        lambda: executor.click_image("item_1") or executor.delay(300),
        delay_ms=200
    )
    
    # 等待奖励
    executor.loop_until(
        lambda: executor.image_exists("reward_popup"),
        lambda: executor.click_image("collect_btn") or executor.delay(1000),
        timeout=30000
    )
    
    executor.log("=== 战斗结束 ===", "INFO")
    return True
```

### 副本循环

```python
def main(executor):
    dungeon_count = 0
    max_dungeons = 10
    
    executor.loop_times(
        max_dungeons,
        lambda: run_dungeon(executor),
        delay_ms=3000
    )
    
    executor.log(f"副本完成，共 {dungeon_count} 次", "INFO")

def run_dungeon(executor):
    # 进入副本
    executor.click_image("enter_btn")
    executor.delay(2000)
    
    # 等待进入战斗
    executor.loop_until(
        lambda: executor.image_exists("boss_hp_bar"),
        lambda: executor.click_image("start_btn") or executor.delay(1000),
        timeout=30000
    )
    
    # 战斗循环
    executor.loop_while(
        lambda: executor.image_exists("boss_hp_bar"),
        lambda: (
            executor.run_script("potion.yaml")
            if executor.image_exists("low_hp_warning")
            else executor.click_image("attack_btn")
        ) or executor.delay(1000),
        max_iterations=100
    )
    
    # 领取奖励
    if executor.wait_image("reward_popup", 5000):
        executor.click_image("reward_popup")
    
    # 退出副本
    executor.click_image("exit_btn")
    executor.delay(2000)
```

## YAML 配置说明

### 完整配置示例

```yaml
meta:
  name: "脚本名称"
  version: "1.0"
  description: "脚本描述"
  created_by: "manual"

config:
  window_title: "游戏窗口标题"
  log_level: "INFO"
  retry_times: 3
  default_timeout: 5000

assets:
  images:
    image_name: "path/to/image.png"

scripts:
  sub_script: "sub_script.yaml"

python_script: "script.py"
```

### 字段说明

| 字段 | 说明 | 必填 |
|------|------|------|
| `meta.name` | 脚本名称 | 是 |
| `meta.version` | 版本号 | 否 |
| `config.window_title` | 游戏窗口标题 | 否 |
| `config.log_level` | 日志等级 | 否 |
| `assets.images` | 图片资源映射 | 否 |
| `python_script` | Python 脚本路径 | 是 |

## 最佳实践

### 1. 使用函数组织代码

```python
def attack(executor):
    executor.click_image("attack_btn")
    executor.delay(1000)

def use_skill(executor):
    executor.click_image("skill_btn")
    executor.delay(2000)

def main(executor):
    executor.loop_while(
        lambda: executor.image_exists("enemy"),
        lambda: attack(executor) or use_skill(executor),
        max_iterations=50
    )
```

### 2. 错误处理

```python
def main(executor):
    try:
        if not executor.wait_image("start_btn", 10000):
            executor.log("未找到开始按钮", "ERROR")
            return False
        
        executor.click_image("start_btn")
        return True
        
    except Exception as e:
        executor.log(f"执行错误：{e}", "ERROR")
        return False
```

### 3. 日志记录

```python
def main(executor):
    executor.log("=== 脚本开始 ===", "INFO")
    
    executor.log("等待 Boss 出现...", "DEBUG")
    if executor.wait_image("boss_hp_bar"):
        executor.log("Boss 出现了！", "INFO")
    else:
        executor.log("等待超时", "WARNING")
    
    executor.log("=== 脚本结束 ===", "INFO")
```

## 注意事项

1. **始终返回布尔值** - `main()` 函数应返回 True（成功）或 False（失败）
2. **设置最大循环次数** - 防止死循环
3. **合理设置超时** - 避免无限等待
4. **使用日志** - 方便调试和监控
5. **循环间隔不要太短** - 建议≥500ms
