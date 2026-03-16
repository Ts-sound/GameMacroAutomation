"""ScreenManager 模块测试"""
import pytest
from src.core.screen import ScreenManager, WindowInfo


class TestWindowInfo:
    def test_window_info_properties(self):
        """测试窗口信息属性"""
        window = WindowInfo(
            title="Test Window",
            left=100,
            top=200,
            width=800,
            height=600
        )
        assert window.title == "Test Window"
        assert window.left == 100
        assert window.top == 200
        assert window.width == 800
        assert window.height == 600
        assert window.right == 900
        assert window.bottom == 800


class TestScreenManager:
    def test_calculate_scale_factor_same_size(self):
        """测试相同尺寸缩放因子"""
        manager = ScreenManager()
        scale = manager.calculate_scale_factor((1920, 1080), (1920, 1080))
        assert scale == 1.0
    
    def test_calculate_scale_factor_smaller(self):
        """测试较小尺寸缩放因子"""
        manager = ScreenManager()
        scale = manager.calculate_scale_factor((1280, 720), (1920, 1080))
        assert scale == pytest.approx(0.666, rel=0.01)
    
    def test_calculate_scale_factor_larger(self):
        """测试较大尺寸缩放因子"""
        manager = ScreenManager()
        scale = manager.calculate_scale_factor((2560, 1440), (1920, 1080))
        assert scale == pytest.approx(1.333, rel=0.01)
    
    def test_calculate_scale_factor_non_uniform(self):
        """测试非均匀缩放 (取较小值)"""
        manager = ScreenManager()
        # 宽度缩放 0.8, 高度缩放 0.5
        scale = manager.calculate_scale_factor((1536, 540), (1920, 1080))
        assert scale == pytest.approx(0.5, rel=0.01)
