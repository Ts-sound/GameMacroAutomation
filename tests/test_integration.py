"""集成测试"""
import pytest
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from src.core.config import ConfigManager, MacroScript, ScriptConfig
from src.core.screen import ScreenManager, WindowInfo
from src.core.image import ImageMatcher, MatchResult
from src.core.lua_bridge import LuaBridge
from src.script.validator import ScriptValidator


class TestIntegrationScriptFlow:
    """测试完整脚本流程"""
    
    def test_script_load_and_validate(self, tmp_path):
        """测试脚本加载和验证"""
        # 创建测试脚本
        script_content = {
            "meta": {
                "name": "Integration Test",
                "version": "1.0",
                "created_by": "test"
            },
            "config": {
                "window_title": "Test Window",
                "log_level": "INFO",
                "retry_times": 3
            },
            "assets": {
                "images": {}
            },
            "lua_script": None
        }
        
        script_file = tmp_path / "test.yaml"
        with open(script_file, 'w') as f:
            yaml.dump(script_content, f)
        
        # 加载脚本
        config_manager = ConfigManager()
        script = config_manager.load_script(str(script_file))
        
        # 验证脚本
        validator = ScriptValidator(scripts_dir=str(tmp_path))
        is_valid, errors = validator.validate_script_file(str(script_file))
        
        assert script.meta.name == "Integration Test"
        assert script.config.window_title == "Test Window"
        assert is_valid
    
    def test_lua_bridge_with_mock_api(self):
        """测试 Lua 桥接与模拟 API"""
        bridge = LuaBridge()
        
        # 注册模拟 API
        call_log = []
        
        def mock_click_image(name: str):
            call_log.append(f"click:{name}")
            return True
        
        def mock_delay(ms: int):
            call_log.append(f"delay:{ms}")
        
        def mock_log(msg: str, level: str = "INFO"):
            call_log.append(f"log:[{level}] {msg}")
        
        bridge.register_functions({
            "click_image": mock_click_image,
            "delay": mock_delay,
            "log": mock_log
        })
        
        # 执行 Lua 脚本
        lua_code = """
        log("Starting test")
        click_image("attack_btn")
        delay(100)
        click_image("skill_1")
        log("Test complete")
        return true
        """
        
        result = bridge.execute_string(lua_code)
        
        assert result is True
        assert "log:[INFO] Starting test" in call_log
        assert "click:attack_btn" in call_log
        assert "delay:100" in call_log
    
    def test_image_matcher_integration(self, tmp_path):
        """测试图像识别集成"""
        from PIL import Image
        import numpy as np
        
        # 创建测试图片
        screen = Image.new('RGB', (200, 200), color='white')
        # 绘制红色方块
        for x in range(50, 100):
            for y in range(50, 100):
                screen.putpixel((x, y), (255, 0, 0))
        
        # 创建模板
        template = Image.new('RGB', (50, 50), color=(255, 0, 0))
        template_path = tmp_path / "template.png"
        template.save(template_path)
        
        # 测试匹配
        matcher = ImageMatcher()
        template_data = matcher.load_template(str(template_path))
        
        assert template_data is not None
        
        result = matcher.find_template(screen, template_data, confidence=0.9)
        
        assert result is not None
        assert result.confidence >= 0.9
        assert abs(result.x - 50) < 5
        assert abs(result.y - 50) < 5
    
    def test_screen_manager_window_info(self):
        """测试窗口信息管理"""
        window = WindowInfo(
            title="Test",
            left=100,
            top=200,
            width=800,
            height=600
        )
        
        assert window.right == 900
        assert window.bottom == 800
        
        screen_manager = ScreenManager()
        size = screen_manager.get_window_size(window)
        
        assert size == (800, 600)
    
    def test_config_manager_roundtrip(self, tmp_path):
        """测试配置管理器读写循环"""
        # 创建脚本
        original = MacroScript(
            meta={"name": "Roundtrip Test", "version": "1.0"},
            config=ScriptConfig(window_title="Test", log_level="DEBUG"),
            assets={"images": {"attack": "attack.png"}}
        )
        
        # 保存
        config_manager = ConfigManager()
        script_file = tmp_path / "roundtrip.yaml"
        
        # 手动保存为 YAML
        data = {
            "meta": {"name": "Roundtrip Test", "version": "1.0"},
            "config": {"window_title": "Test", "log_level": "DEBUG"},
            "assets": {"images": {"attack": "attack.png"}}
        }
        
        with open(script_file, 'w') as f:
            yaml.dump(data, f)
        
        # 加载
        loaded = config_manager.load_script(str(script_file))
        
        assert loaded.meta.name == "Roundtrip Test"
        assert loaded.config.window_title == "Test"
        assert loaded.config.log_level == "DEBUG"
        assert "attack" in loaded.assets.images


class TestCLICommands:
    """测试 CLI 命令"""
    
    def test_cli_help(self):
        """测试 CLI 帮助"""
        import subprocess
        result = subprocess.run(
            ["python", "-m", "src.main", "--help"],
            capture_output=True,
            text=True
        )
        # 即使依赖未安装也应该显示帮助
        assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()


class TestExecutionReport:
    """测试执行报告"""
    
    def test_report_creation(self):
        """测试报告创建"""
        from src.core.logger import ExecutionReport
        
        report = ExecutionReport(
            script="test.yaml",
            start_time="2026-03-16T10:00:00"
        )
        
        assert report.script == "test.yaml"
        assert report.status == "running"
    
    def test_report_to_yaml(self):
        """测试报告转 YAML"""
        from src.core.logger import ExecutionReport
        
        report = ExecutionReport(
            script="test.yaml",
            start_time="2026-03-16T10:00:00",
            end_time="2026-03-16T10:05:00",
            status="success"
        )
        
        yaml_str = report.to_yaml()
        
        assert "script: test.yaml" in yaml_str
        assert "status: success" in yaml_str
