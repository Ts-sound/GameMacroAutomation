"""ScriptValidator 模块测试"""
import pytest
import yaml
from pathlib import Path
from src.script.validator import ScriptValidator, ValidationError


class TestScriptValidator:
    def test_validate_valid_script(self, tmp_path):
        """测试验证有效脚本"""
        # 创建测试脚本
        script_content = {
            "meta": {"name": "Test Script"},
            "config": {"window_title": "Test"},
            "assets": {"images": {}},
            "lua_script": None
        }
        
        script_file = tmp_path / "test.yaml"
        with open(script_file, 'w') as f:
            yaml.dump(script_content, f)
        
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(script_file))
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_missing_meta(self, tmp_path):
        """测试验证缺少 meta"""
        script_content = {
            "config": {"window_title": "Test"}
        }
        
        script_file = tmp_path / "test.yaml"
        with open(script_file, 'w') as f:
            yaml.dump(script_content, f)
        
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(script_file))
        
        assert not is_valid
        assert any("meta.name" in e for e in errors)
    
    def test_validate_file_not_exists(self, tmp_path):
        """测试验证不存在的文件"""
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(tmp_path / "nonexistent.yaml"))
        
        assert not is_valid
        assert any("文件不存在" in e for e in errors)
    
    def test_validate_missing_subscript(self, tmp_path):
        """测试验证缺少子脚本"""
        script_content = {
            "meta": {"name": "Test"},
            "scripts": {"attack": "attack.yaml"}
        }
        
        script_file = tmp_path / "test.yaml"
        with open(script_file, 'w') as f:
            yaml.dump(script_content, f)
        
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(script_file))
        
        assert not is_valid
        assert any("子脚本不存在" in e for e in errors)
    
    def test_show_dependency_tree(self, tmp_path):
        """测试显示依赖树"""
        # 创建主脚本
        main_script = {
            "meta": {"name": "Main Script"},
            "config": {},
            "assets": {"images": {}},
            "scripts": {"sub": "sub.yaml"}
        }
        
        # 创建子脚本
        sub_script = {
            "meta": {"name": "Sub Script"},
            "config": {},
            "assets": {"images": {}}
        }
        
        main_file = tmp_path / "main.yaml"
        sub_file = tmp_path / "sub.yaml"
        
        with open(main_file, 'w') as f:
            yaml.dump(main_script, f)
        with open(sub_file, 'w') as f:
            yaml.dump(sub_script, f)
        
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        tree = validator.show_dependency_tree(str(main_file))
        
        assert "Main Script" in tree
        assert "Sub Script" in tree
