# 项目规范

## 技术栈

- **语言：** Python 3.10+
- **目标平台：** Windows only
- **构建工具：** setuptools + pyproject.toml
- **依赖库：** pyautogui, pynput, Pillow, pyyaml, pygetwindow, pydantic

## 目录结构

```
src/
├── core/           # 核心模块（screen, input, image, config, logger）
├── recorder/       # 录制器模块
├── executor/       # 执行器模块（executor, api）
├── script/         # 脚本验证模块（validator, schema）
└── tools/          # 辅助工具模块（zone_captor）

docs/
├── design/         # 设计文档
│   ├── README.md   # 系统总体设计
│   └── <module>/   # 各模块设计
├── plans/          # 实施计划
├── requirements.md # 需求文档
└── terminology.md  # 术语定义

scripts/            # 用户脚本目录
assets/             # 资源目录
├── templates/      # 动作模板
└── detection/      # 检测区域
tests/              # 测试目录
logs/               # 日志输出
```

## 编码规范

- **代码格式化：** black (line-length: 300)
- **代码检查：** ruff
- **类型检查：** mypy
- **测试框架：** pytest
- **行长度：** 300 字符

## 命令

```bash
# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest

# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/

# CLI 命令
python -m src.main record -o scripts/test.yaml -w "窗口标题" -s 400
python -m src.main run scripts/test.yaml -w "窗口标题"
python -m src.main validate scripts/test.yaml
python -m src.main capture-zone --output assets/detection/xxx.png
```

## 脚本架构

- **YAML 层：** 元数据、配置、资源引用、检测区域定义
- **Python 层：** 流程控制、条件判断、循环、子脚本调用

## 设计文档要求

- 使用 mermaid 图表
- 模块文档包含：Overview, Architecture (graph TD), Interfaces, Key Sequences (sequenceDiagram), Error Handling, Testing Strategy
- 总体设计文档包含：Overview, Architecture, Modules, Technical Decisions, Data Model, API Design, Security Considerations, Deployment

## 变更规范

- 添加新功能 → 更新设计文档 → 编写实施计划 → 实现
- 修复 bug → 验证设计文档是否仍准确 → 如需更新则更新
- 提交前确保测试通过
- 使用清晰的提交信息