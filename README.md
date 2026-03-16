# Game Macro Automation

游戏宏自动化系统 - 基于 Python + Lua 的 Windows 游戏宏工具

## 功能特性

- **录制生成**: 录制鼠标键盘操作，生成基础单元脚本
- **Lua 编排**: 使用 Lua 编写复杂流程逻辑
- **图像识别**: OpenCV 模板匹配，自动 UI 定位
- **分辨率适配**: 自动检测窗口分辨率，计算缩放因子
- **层级调用**: 脚本可调用其他脚本，形成层级结构
- **详细日志**: 可配置日志等级，执行报告生成

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 录制脚本

```bash
python -m src.main record --output scripts/attack.yaml
```

### 运行脚本

```bash
python -m src.main run scripts/entry_dungeon.yaml
```

### 截图检测区域

```bash
python -m src.main capture-zone --output assets/detection/boss_hp.png
```

## 脚本示例

### YAML 配置 (attack.yaml)

```yaml
meta:
  name: "攻击动作"
  version: "1.0"

config:
  window_title: "游戏窗口"
  log_level: "INFO"

assets:
  images:
    target: "assets/attack_btn.png"

lua_script: "scripts/attack.lua"
```

### Lua 逻辑 (attack.lua)

```lua
function main()
    wait_image("target", 3000)
    click_image("target")
    delay(200)
end
```

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/
```
