"""脚本验证器"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
from src.core.config import ConfigManager, MacroScript


class ValidationError(Exception):
    """验证错误"""
    pass


class ScriptValidator:
    """脚本验证器"""
    
    def __init__(self, scripts_dir: str = "scripts"):
        self.scripts_dir = Path(scripts_dir)
        self._logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
    
    def validate_script_file(self, yaml_path: str) -> Tuple[bool, List[str]]:
        """
        验证脚本文件
        
        Args:
            yaml_path: YAML 文件路径
        
        Returns:
            (是否通过，错误列表)
        """
        errors = []
        
        # 检查文件存在
        if not Path(yaml_path).exists():
            errors.append(f"文件不存在：{yaml_path}")
            return (False, errors)
        
        # 加载脚本
        try:
            script = self.config_manager.load_script(yaml_path)
        except Exception as e:
            errors.append(f"YAML 解析失败：{e}")
            return (False, errors)
        
        # 验证 meta
        if not script.meta.name:
            errors.append("缺少必需的 meta.name 字段")
        
        # 验证 Python 脚本存在
        if script.python_script:
            python_path = Path(yaml_path).parent / script.python_script
            if not python_path.exists():
                errors.append(f"Python 脚本不存在：{python_path}")
        
        # 验证子脚本引用
        for name, sub_script in script.scripts.items():
            sub_path = self.scripts_dir / sub_script
            if not sub_path.exists():
                errors.append(f"子脚本不存在 [{name}]: {sub_path}")
        
        # 验证图片资源
        for name, img_path in script.assets.images.items():
            full_path = Path(img_path)
            if not full_path.is_absolute():
                full_path = Path(yaml_path).parent / full_path
            if not full_path.exists():
                errors.append(f"图片资源不存在 [{name}]: {full_path}")
        
        # 验证检测区域
        for name, zone in script.detection_zones.items():
            if 'image' not in zone:
                errors.append(f"检测区域缺少 image [{name}]")
                continue
            
            img_path = zone['image']
            full_path = Path(img_path)
            if not full_path.is_absolute():
                full_path = Path(yaml_path).parent / full_path
            if not full_path.exists():
                errors.append(f"检测图片不存在 [{name}]: {full_path}")
        
        is_valid = len(errors) == 0
        return (is_valid, errors)
    
    def show_dependency_tree(
        self,
        yaml_path: str,
        indent: int = 0,
        visited: Optional[set] = None
    ) -> str:
        """显示脚本依赖树"""
        if visited is None:
            visited = set()
        
        script = self.config_manager.load_script(yaml_path)
        name = script.meta.name or Path(yaml_path).name
        
        tree = "  " * indent + f"├─ {name}\n"
        
        # 添加子脚本
        for sub_name, sub_path in script.scripts.items():
            full_path = self.scripts_dir / sub_path
            path_str = str(full_path)
            
            if path_str in visited:
                tree += "  " * (indent + 1) + f"├─ {sub_name} (循环引用)\n"
            else:
                visited.add(path_str)
                tree += self.show_dependency_tree(path_str, indent + 1, visited)
        
        # 添加 Python 脚本
        if script.python_script:
            tree += "  " * (indent + 1) + f"├─ {script.python_script} (Python)\n"
        
        return tree


# CLI 辅助函数
def validate_script_file(yaml_path: str):
    """CLI: 验证脚本"""
    validator = ScriptValidator()
    is_valid, errors = validator.validate_script_file(yaml_path)
    
    if is_valid:
        print(f"✓ 脚本验证通过：{yaml_path}")
    else:
        print(f"✗ 脚本验证失败：{yaml_path}")
        for error in errors:
            print(f"  - {error}")


def show_script_tree(yaml_path: str):
    """CLI: 显示依赖树"""
    validator = ScriptValidator()
    tree = validator.show_dependency_tree(yaml_path)
    print(tree)
