"""配置管理模块"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Any
from pathlib import Path
import yaml


@dataclass
class ScriptMeta:
    """脚本元数据"""
    name: str = ""
    version: str = "1.0"
    description: str = ""
    created_by: str = "manual"  # recorder/manual


@dataclass
class ScriptConfig:
    """脚本配置"""
    window_title: Optional[str] = None
    screen_region: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    scale_factor: Optional[float] = None
    reference_resolution: Tuple[int, int] = field(default=(1920, 1080))
    log_level: str = "INFO"
    log_file: Optional[str] = None
    log_console: bool = True
    on_error: str = "stop"  # stop/retry/ignore
    retry_times: int = 3
    default_timeout: int = 5000  # ms
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScriptConfig':
        """从字典创建配置"""
        if data is None:
            return cls()
        
        # 处理 screen_region 元组
        screen_region = data.get('screen_region')
        if isinstance(screen_region, list):
            screen_region = tuple(screen_region)
        
        return cls(
            window_title=data.get('window_title'),
            screen_region=screen_region,
            scale_factor=data.get('scale_factor'),
            reference_resolution=tuple(data.get('reference_resolution', (1920, 1080))),
            log_level=data.get('log_level', 'INFO'),
            log_file=data.get('log_file'),
            log_console=data.get('log_console', True),
            on_error=data.get('on_error', 'stop'),
            retry_times=data.get('retry_times', 3),
            default_timeout=data.get('default_timeout', 5000)
        )


@dataclass
class ScriptAssets:
    """脚本资源"""
    images: dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScriptAssets':
        """从字典创建资源"""
        if data is None:
            return cls()
        return cls(images=data.get('images', {}))


@dataclass
class MacroScript:
    """宏脚本完整结构"""
    meta: ScriptMeta
    config: ScriptConfig
    assets: ScriptAssets
    python_script: Optional[str] = None  # Python 脚本路径
    scripts: dict[str, str] = field(default_factory=dict)  # 子脚本引用
    detection_zones: dict[str, dict] = field(default_factory=dict)
    actions: List[dict] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)  # 原始 YAML 数据
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MacroScript':
        """从 YAML 字典创建"""
        return cls(
            meta=ScriptMeta(**data.get('meta', {})),
            config=ScriptConfig.from_dict(data.get('config', {})),
            assets=ScriptAssets.from_dict(data.get('assets', {})),
            python_script=data.get('python_script'),
            scripts=data.get('scripts', {}),
            detection_zones=data.get('detection_zones', {}),
            actions=data.get('actions', []),
            raw_data=data
        )


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)
    
    def load_script_config(self, yaml_path: str) -> ScriptConfig:
        """加载脚本配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return ScriptConfig.from_dict(data.get('config', {}))
    
    def load_script(self, yaml_path: str) -> MacroScript:
        """
        加载完整脚本
        
        Args:
            yaml_path: YAML 文件路径
        
        Returns:
            MacroScript 对象
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return MacroScript.from_dict(data)
    
    def save_script(self, script: MacroScript, yaml_path: str):
        """保存脚本到 YAML 文件"""
        # 使用 raw_data 保持格式
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(script.raw_data, f, allow_unicode=True, default_flow_style=False)
    
    def list_scripts(self, scripts_dir: str) -> List[str]:
        """列出所有可用脚本"""
        scripts = []
        scripts_path = Path(scripts_dir)
        
        if not scripts_path.exists():
            return scripts
        
        for yaml_file in scripts_path.glob("*.yaml"):
            scripts.append(yaml_file.name)
        
        return sorted(scripts)
