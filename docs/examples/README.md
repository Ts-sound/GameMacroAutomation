# 示例项目

本目录包含完整的游戏宏自动化示例，每个示例都是独立的。

## 示例列表

### 01_loop_demo - 循环控制演示

**难度**: 入门 ⭐

**功能**:
- 使用 `wait_image()` 等待目标出现
- 使用 `loop_while()` 进行条件循环
- 使用 `run_script()` 调用子脚本

**运行**:
```bash
python -m src.main run docs/examples/01_loop_demo/main.yaml
```

**说明**: 详见 [01_loop_demo/README.md](01_loop_demo/README.md)

---

### 02_battle_example - 战斗流程示例

**难度**: 进阶 ⭐⭐

**功能**:
- 多阶段战斗流程
- 使用 `loop_while()` 条件循环（Boss 存在时攻击）
- 使用 `loop_times()` 固定次数循环（拾取物品）
- 使用 `loop_until()` 直到条件满足（等待奖励）
- 条件判断和分支逻辑

**运行**:
```bash
python -m src.main run docs/examples/02_battle_example/battle_loop.yaml
```

**说明**: 详见 [02_battle_example/README.md](02_battle_example/README.md)

---

## 运行所有示例

```bash
# 示例 1: 循环控制
python -m src.main run docs/examples/01_loop_demo/main.yaml

# 示例 2: 战斗流程
python -m src.main run docs/examples/02_battle_example/battle_loop.yaml
```

## 注意事项

1. **窗口配置**: 示例中的 `window_title` 需要修改为实际的游戏窗口
2. **图片资源**: 示例引用的图片需要根据实际情况准备或重新录制
3. **子脚本**: 部分示例引用了子脚本，需要创建相应的子脚本文件

## 创建自己的脚本

详见 [Python 脚本使用指南](../python_script_guide.md)
