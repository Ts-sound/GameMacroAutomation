"""InputController 模块测试"""
import pytest
from unittest.mock import patch
from src.core.input import InputController, RecordedAction, InputRecorder


class TestRecordedAction:
    def test_action_creation(self):
        """测试录制动作创建"""
        action = RecordedAction(
            timestamp=1000,
            action_type="mouse_click",
            x=100,
            y=200,
            button="left"
        )
        assert action.timestamp == 1000
        assert action.x == 100
        assert action.y == 200
        assert action.button == "left"
        assert action.key is None
    
    def test_action_with_key(self):
        """测试按键动作"""
        action = RecordedAction(
            timestamp=500,
            action_type="key_press",
            key="space"
        )
        assert action.key == "space"
        assert action.x is None


class TestInputController:
    def test_scale_coordinates(self):
        """测试坐标缩放"""
        controller = InputController(scale_factor=0.5)
        scaled = controller.scale_coordinates(100, 200)
        assert scaled == (50, 100)
    
    def test_scale_coordinates_default(self):
        """测试默认缩放因子"""
        controller = InputController()
        scaled = controller.scale_coordinates(100, 200)
        assert scaled == (100, 200)
    
    def test_click(self):
        """测试点击"""
        controller = InputController(scale_factor=0.5)
        with patch('pyautogui.click') as mock_click:
            controller.click(100, 200, button='left')
            mock_click.assert_called_once_with(x=50, y=100, button='left')
    
    def test_press_no_duration(self):
        """测试无持续时间按键"""
        controller = InputController()
        with patch('pyautogui.press') as mock_press:
            controller.press('space')
            mock_press.assert_called_once_with('space')
    
    def test_delay(self):
        """测试延迟"""
        controller = InputController()
        with patch('time.sleep') as mock_sleep:
            controller.delay(100)
            mock_sleep.assert_called_once_with(0.1)


class TestInputRecorder:
    def test_recorder_init(self):
        """测试录制器初始化"""
        from src.core.screen import ScreenManager
        manager = ScreenManager()
        recorder = InputRecorder(manager)
        assert recorder.is_recording == False
        assert len(recorder.actions) == 0
    
    def test_get_relative_time_before_start(self):
        """测试开始前相对时间"""
        from src.core.screen import ScreenManager
        manager = ScreenManager()
        recorder = InputRecorder(manager)
        assert recorder._get_relative_time() == 0
