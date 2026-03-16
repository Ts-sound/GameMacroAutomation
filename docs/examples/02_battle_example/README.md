# 战斗流程示例

演示完整的战斗循环流程，包含多种循环控制。

## 运行方式

```bash
python -m src.main run docs/examples/02_battle_example/battle_loop.yaml
```

## 功能演示

- 多阶段战斗流程
- 使用 `loop_while()` 条件循环（Boss 存在时攻击）
- 使用 `loop_times()` 固定次数循环（拾取物品）
- 使用 `loop_until()` 直到条件满足（等待奖励）
- 条件判断和分支逻辑

## 文件说明

| 文件 | 说明 |
|------|------|
| `battle_loop.py` | 战斗流程 Python 脚本 |
| `battle_loop.yaml` | YAML 配置文件 |

## 核心代码

```python
def main(executor):
    executor.log("=== 战斗开始 ===", "INFO")
    
    # 等待 Boss 出现
    if not executor.wait_image("boss_hp_bar", 10000):
        return False
    
    # 条件循环：Boss 存在时持续攻击
    executor.loop_while(
        lambda: executor.image_exists("boss_hp_bar"),
        lambda: (
            executor.run_script("potion.yaml") 
            if executor.image_exists("low_hp_warning")
            else executor.click_image("attack_btn")
        ) or executor.delay(1000),
        max_iterations=100
    )
    
    # 固定次数循环：拾取 5 次物品
    executor.loop_times(5, lambda: ..., delay_ms=200)
    
    # 直到条件满足：等待奖励弹窗
    executor.loop_until(
        lambda: executor.image_exists("reward_popup"),
        lambda: ...,
        timeout=30000
    )
    
    return True
```

## 配置说明

```yaml
config:
  window_title: "游戏窗口"  # 修改为实际窗口
  log_level: "INFO"

assets:
  images:
    boss_hp_bar: "assets/templates/boss_hp.png"
    attack_btn: "assets/templates/attack_btn.png"
    # ... 更多图片

python_script: "battle_loop.py"
```

## 注意事项

1. **窗口配置**: 使用前请修改 `window_title` 为实际游戏窗口
2. **图片资源**: 需要准备好相应的模板图片在 `assets/templates/` 目录
3. **子脚本**: 示例引用了 `potion.yaml`，需要创建相应的子脚本或移除引用
