"""ConfigManager 模块测试"""
import pytest
import yaml
from pathlib import Path
from src.core.config import (
    ConfigManager, ScriptConfig, ScriptMeta, 
    ScriptAssets, MacroScript
)


class TestScriptMeta:
    def test_default_values(self):
        """测试默认值"""
        meta = ScriptMeta()
        assert meta.name == ""
        assert meta.version == "1.0"
        assert meta.created_by == "manual"


class TestScriptConfig:
    def test_default_config(self):
        """测试默认配置"""
        config = ScriptConfig()
        assert config.window_title is None
        assert config.log_level == "INFO"
        assert config.retry_times == 3
        assert config.reference_resolution == (1920, 1080)
    
    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "window_title": "Test Window",
            "log_level": "DEBUG",
            "retry_times": 5
        }
        config = ScriptConfig.from_dict(data)
        assert config.window_title == "Test Window"
        assert config.log_level == "DEBUG"
        assert config.retry_times == 5
    
    def test_config_from_dict_empty(self):
        """测试从空字典创建配置"""
        config = ScriptConfig.from_dict({})
        assert config.log_level == "INFO"
        assert config.retry_times == 3


class TestScriptAssets:
    def test_default_assets(self):
        """测试默认资源"""
        assets = ScriptAssets()
        assert assets.images == {}
    
    def test_assets_from_dict(self):
        """测试从字典创建资源"""
        data = {"images": {"attack": "attack.png"}}
        assets = ScriptAssets.from_dict(data)
        assert assets.images["attack"] == "attack.png"


class TestMacroScript:
    def test_from_dict(self):
        """测试从字典创建脚本"""
        data = {
            "meta": {"name": "Test Script"},
            "config": {"log_level": "DEBUG"},
            "assets": {"images": {}}
        }
        script = MacroScript.from_dict(data)
        assert script.meta.name == "Test Script"
        assert script.config.log_level == "DEBUG"


class TestConfigManager:
    def test_load_script_config(self, tmp_path):
        """测试加载脚本配置"""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("window_title: Test\nlog_level: DEBUG\n")
        
        manager = ConfigManager()
        config = manager.load_script_config(str(config_file))
        assert config.window_title == "Test"
        assert config.log_level == "DEBUG"
    
    def test_load_script(self, tmp_path):
        """测试加载完整脚本"""
        script_file = tmp_path / "script.yaml"
        content = {
            "meta": {"name": "Test"},
            "config": {},
            "assets": {"images": {}}
        }
        script_file.write_text(yaml.dump(content))
        
        manager = ConfigManager()
        script = manager.load_script(str(script_file))
        assert script.meta.name == "Test"
    
    def test_list_scripts(self, tmp_path):
        """测试列出脚本"""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "attack.yaml").touch()
        (scripts_dir / "defend.yaml").touch()
        
        manager = ConfigManager()
        scripts = manager.list_scripts(str(scripts_dir))
        assert scripts == ["attack.yaml", "defend.yaml"]
