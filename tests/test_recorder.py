"""ScriptRecorder 模块测试"""
import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
from src.recorder.recorder import ScriptRecorder
from src.core.input import RecordedAction


class TestScriptRecorder:
    def test_init(self, tmp_path):
        """测试初始化"""
        recorder = ScriptRecorder(output_dir=str(tmp_path))
        assert recorder.output_dir == tmp_path
    
    def test_generate_script_name(self, tmp_path):
        """测试生成脚本名称"""
        recorder = ScriptRecorder(output_dir=str(tmp_path))
        name = recorder.generate_script_name("test")
        assert name.startswith("test_")
    
    def test_actions_to_yaml_basic(self, tmp_path):
        """测试动作转 YAML"""
        recorder = ScriptRecorder(output_dir=str(tmp_path))
        
        actions = [
            RecordedAction(timestamp=0, action_type="mouse_click", x=100, y=200, button="left"),
            RecordedAction(timestamp=500, action_type="key_press", key="space")
        ]
        
        yaml_data = recorder.actions_to_yaml(actions, "Test Window")
        
        assert yaml_data["meta"]["created_by"] == "recorder"
        assert yaml_data["config"]["window_title"] == "Test Window"
        assert len(yaml_data["actions"]) >= 2
    
    def test_actions_to_yaml_with_delay(self, tmp_path):
        """测试动作转 YAML 添加延迟"""
        recorder = ScriptRecorder(output_dir=str(tmp_path))
        
        actions = [
            RecordedAction(timestamp=0, action_type="mouse_click", x=100, y=200, button="left"),
            RecordedAction(timestamp=1000, action_type="mouse_click", x=150, y=250, button="left")
        ]
        
        yaml_data = recorder.actions_to_yaml(actions, "Test Window")
        
        # 应该有 delay 动作
        action_types = [a.get("type") for a in yaml_data["actions"]]
        assert "delay" in action_types
    
    def test_save_script(self, tmp_path):
        """测试保存脚本"""
        recorder = ScriptRecorder(output_dir=str(tmp_path))
        
        yaml_data = {
            "meta": {"name": "Test"},
            "config": {},
            "assets": {"images": {}},
            "actions": []
        }
        
        script_path = recorder.save_script(yaml_data, "test_script")
        
        assert Path(script_path).exists()
        
        with open(script_path) as f:
            loaded = yaml.safe_load(f)
        
        assert loaded["meta"]["name"] == "Test"
