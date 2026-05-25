"""ScreenManager 模块测试"""

from unittest.mock import patch

import pytest

from src.core.screen import ScreenManager, WindowInfo


class TestWindowInfo:
    def test_window_info_properties(self):
        """测试窗口信息属性"""
        window = WindowInfo(
            title="Test Window", left=100, top=200, width=800, height=600
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

    def test_get_screen_by_id_default(self):
        """测试主屏幕默认值"""
        manager = ScreenManager()
        with patch.object(manager, "get_screen_by_id", return_value=None):
            result = manager.get_screen_by_id(0)
        assert result == (1920, 1080)

    def test_region_to_absolute_full_screen(self):
        """测试全屏百分比区域"""
        manager = ScreenManager()
        with patch.object(manager, "get_screen_by_id", return_value=(1920, 1080)):
            result = manager.region_to_absolute({"x": (0.0, 1.0), "y": (0.0, 1.0)})
        assert result == (0, 0, 1920, 1080)

    def test_region_to_absolute_half_screen(self):
        """测试半屏百分比区域"""
        manager = ScreenManager()
        with patch.object(manager, "get_screen_by_id", return_value=(1920, 1080)):
            result = manager.region_to_absolute({"x": (0.0, 0.5), "y": (0.0, 1.0)})
        assert result == (0, 0, 960, 1080)

    def test_region_to_absolute_center_region(self):
        """测试中心区域百分比"""
        manager = ScreenManager()
        with patch.object(manager, "get_screen_by_id", return_value=(1920, 1080)):
            result = manager.region_to_absolute({"x": (0.4, 0.6), "y": (0.1, 0.2)})
        assert result == (768, 108, 384, 108)

    def test_region_to_absolute_with_screen_id(self):
        """测试指定屏幕 ID"""
        manager = ScreenManager()
        with patch.object(
            manager, "get_screen_by_id", return_value=(2560, 1440)
        ) as mock:
            result = manager.region_to_absolute(
                {"x": (0.0, 0.5), "y": (0.0, 1.0)}, screen_id=1
            )
            mock.assert_called_with(1)
        assert result == (0, 0, 1280, 1440)

    def test_region_to_absolute_fallback(self):
        """测试屏幕不存在时回退到 get_screen_size"""
        manager = ScreenManager()
        with patch.object(manager, "get_screen_by_id", return_value=None):
            with patch.object(manager, "get_screen_size", return_value=(1920, 1080)):
                result = manager.region_to_absolute({"x": (0.0, 1.0), "y": (0.0, 1.0)})
        assert result == (0, 0, 1920, 1080)
