# Script 模块设计

## 概述

Script 模块负责 YAML 脚本的 Schema 定义、验证和管理。

## 模块结构

```
src/script/
├── __init__.py
├── schema.py          # YAML Schema 定义
├── validator.py       # 脚本验证器
└── manager.py         # 脚本管理（待实现）
```

## 组件设计

### 1. Schema 定义 (schema.py)

**职责：** 定义 YAML 脚本的结构和数据类型

**常量定义：**
```python
# 动作类型定义
ACTION_TYPES = Literal[
    "click", "click_image", "keypress", "type_text",
    "delay", "wait_image", "wait_image_disappear",
    "move_mouse", "scroll", "log", "run_script",
    "conditional", "loop", "parallel", "sequence"
]

# 条件类型定义
CONDITION_TYPES = Literal[
    "image_exists", "image_not_exists", "timeout", "custom"
]

# Schema 验证规则
SCRIPT_SCHEMA = {
    "meta": {
        "required": True,
        "fields": {
            "name": {"type": str, "required": True},
            "version": {"type": str, "required": False},
            ...
        }
    },
    "config": {...},
    "assets": {...},
    ...
}
```

---

### 2. ScriptValidator (validator.py)

**职责：** 验证 YAML 脚本的完整性和正确性

**类设计：**
```python
class ValidationError(Exception):
    """验证错误异常"""

class ScriptValidator:
    __init__(scripts_dir="scripts")
    
    validate_script_file(yaml_path) -> Tuple[bool, List[str]]
    show_dependency_tree(yaml_path, indent, visited) -> str

# CLI 辅助函数
validate_script_file(yaml_path)
show_script_tree(yaml_path)
```

**验证规则：**

| 检查项 | 说明 |
|--------|------|
| 文件存在 | YAML 文件必须存在 |
| YAML 解析 | 必须是有效的 YAML 格式 |
| meta.name | 必需的元数据字段 |
| python_script | 如果引用，文件必须存在 |
| scripts.* | 子脚本引用必须存在 |
| assets.images.* | 图片资源必须存在 |
| detection_zones.*.image | 检测图片必须存在 |

**依赖树显示：**
```
entry_dungeon.yaml
├─ enter_dungeon.yaml
│  ├─ click_start.yaml
│  └─ confirm.yaml
├─ battle_loop.yaml
│  ├─ attack.yaml
│  └─ skill_combo.yaml
└─ collect_reward.yaml
```

---

### 3. ScriptManager (manager.py) - 待实现

**职责：** 脚本列表、依赖分析、批量操作

**计划功能：**
```python
class ScriptManager:
    __init__(scripts_dir, assets_dir)
    
    list_scripts() -> List[Dict]
    get_script_info(script_name) -> Dict
    get_dependencies(script_name) -> List[str]
    get_dependents(script_name) -> List[str]
    validate_all() -> Dict[str, Tuple[bool, List[str]]]
```

## YAML 脚本格式

### 完整示例

```yaml
meta:
  name: "副本流程"
  version: "1.0"
  description: "完整副本自动化流程"
  created_by: "manual"

config:
  window_title: "游戏窗口"
  screen_region: [0, 0, 1920, 1080]
  scale_factor: null
  log_level: "INFO"
  default_timeout: 5000
  on_error: "stop"

assets:
  images:
    attack_btn: "assets/attack_btn.png"
    boss_hp: "assets/boss_hp.png"

scripts:
  attack: "attack.yaml"
  potion: "potion.yaml"

detection_zones:
  boss_hp_bar:
    image: "detection/boss_hp.png"
    confidence: 0.85
    region: [100, 50, 200, 30]

python_script: "scripts/dungeon_flow.py"
```

### 字段说明

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `meta.name` | ✅ | string | 脚本名称 |
| `meta.version` | ❌ | string | 版本号 |
| `meta.description` | ❌ | string | 描述 |
| `meta.created_by` | ❌ | string | recorder/manual |
| `config.window_title` | ❌ | string | 窗口标题 |
| `config.log_level` | ❌ | string | 日志等级 |
| `config.on_error` | ❌ | string | 错误处理策略 |
| `assets.images` | ❌ | dict | 图片资源映射 |
| `scripts` | ❌ | dict | 子脚本引用 |
| `detection_zones` | ❌ | dict | 检测区域定义 |
| `python_script` | ❌ | string | Python 脚本路径 |
| `actions` | ❌ | list | 动作序列（纯 YAML 执行） |

## 依赖关系

```
ScriptValidator
├── ConfigManager (core/config.py)
└── Path (stdlib)

ScriptManager (待实现)
├── ScriptValidator
├── ConfigManager
└── yaml (stdlib)
```

## 使用示例

### 验证脚本

```python
from src.script.validator import ScriptValidator

validator = ScriptValidator(scripts_dir="scripts")
is_valid, errors = validator.validate_script_file("scripts/entry_dungeon.yaml")

if not is_valid:
    for error in errors:
        print(f"错误：{error}")
```

### 显示依赖树

```python
from src.script.validator import show_script_tree

tree = show_script_tree("scripts/entry_dungeon.yaml")
print(tree)
```

### CLI 使用

```bash
# 验证单个脚本
python -m src.main validate scripts/entry_dungeon.yaml

# 显示依赖树
python -m src.main tree scripts/entry_dungeon.yaml

# 列出所有脚本
python -m src.main list
```

## 错误处理

### 验证错误类型

| 错误类型 | 说明 | 示例 |
|---------|------|------|
| 文件不存在 | YAML 或引用的文件不存在 | `文件不存在：scripts/attack.yaml` |
| YAML 解析失败 | YAML 格式错误 | `YAML 解析失败：invalid syntax` |
| 缺少必需字段 | 缺少 meta.name 等 | `缺少必需的 meta.name 字段` |
| 资源不存在 | 图片或子脚本不存在 | `图片资源不存在 [attack]: assets/attack.png` |

## 测试

```python
# tests/test_validator.py
class TestScriptValidator:
    def test_validate_valid_script(self, tmp_path)
    def test_validate_missing_meta(self, tmp_path)
    def test_validate_file_not_exists(self, tmp_path)
    def test_validate_missing_subscript(self, tmp_path)
    def test_show_dependency_tree(self, tmp_path)
```
