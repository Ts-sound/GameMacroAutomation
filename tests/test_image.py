"""ImageMatcher 模块测试"""
import pytest
from pathlib import Path
from src.core.image import ImageMatcher, MatchResult


class TestMatchResult:
    def test_center_property(self):
        """测试匹配区域中心点"""
        result = MatchResult(x=100, y=100, width=50, height=50, confidence=0.9)
        assert result.center == (125, 125)


class TestImageMatcher:
    def test_init_default_confidence(self):
        """测试默认置信度"""
        matcher = ImageMatcher()
        assert matcher.default_confidence == 0.8
    
    def test_init_custom_confidence(self):
        """测试自定义置信度"""
        matcher = ImageMatcher(default_confidence=0.9)
        assert matcher.default_confidence == 0.9
    
    def test_load_template_not_exists(self, tmp_path):
        """测试加载不存在的模板"""
        matcher = ImageMatcher()
        result = matcher.load_template(str(tmp_path / "nonexistent.png"))
        assert result is None
    
    def test_load_template_and_cache(self, tmp_path):
        """测试加载模板并缓存"""
        from PIL import Image
        test_img = Image.new('RGB', (50, 50), color='red')
        template_path = tmp_path / "test.png"
        test_img.save(template_path)
        
        matcher = ImageMatcher()
        template = matcher.load_template(str(template_path))
        assert template is not None
        
        # 测试缓存
        template2 = matcher.load_template(str(template_path))
        assert template2 is template
    
    def test_clear_cache(self, tmp_path):
        """测试清除缓存"""
        from PIL import Image
        test_img = Image.new('RGB', (50, 50), color='red')
        template_path = tmp_path / "test.png"
        test_img.save(template_path)
        
        matcher = ImageMatcher()
        matcher.load_template(str(template_path))
        matcher.clear_cache()
        
        # 缓存清除后可以再次加载
        template2 = matcher.load_template(str(template_path))
        assert template2 is not None
