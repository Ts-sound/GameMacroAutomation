"""图像识别模块 - 使用 pyautogui 进行模板匹配"""
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
import pyautogui
from PIL import Image


@dataclass
class MatchResult:
    """匹配结果"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    @property
    def center(self) -> tuple[int, int]:
        """返回匹配区域中心点"""
        return (self.x + self.width // 2, self.y + self.height // 2)


class ImageMatcher:
    """图像匹配器 - 使用 pyautogui.locateCenterOnScreen"""
    
    def __init__(self, default_confidence: float = 0.8):
        """
        Args:
            default_confidence: 默认匹配置信度阈值
        """
        self.default_confidence = default_confidence
        self._template_cache: dict[str, Image.Image] = {}
    
    def load_template(self, path: str) -> Optional[Image.Image]:
        """
        加载模板图片
        
        Args:
            path: 图片路径
        
        Returns:
            PIL Image 或 None
        """
        # 检查缓存
        if path in self._template_cache:
            return self._template_cache[path]
        
        # 加载图片
        if not Path(path).exists():
            return None
        
        # 加载并缓存
        pil_img = Image.open(path)
        self._template_cache[path] = pil_img
        return pil_img
    
    def clear_cache(self):
        """清除模板缓存"""
        self._template_cache.clear()
    
    def find_template(
        self,
        screen: Image.Image,
        template: Image.Image,
        confidence: Optional[float] = None
    ) -> Optional[MatchResult]:
        """
        在屏幕图像中查找模板
        
        注意：此方法会临时保存截图并调用 pyautogui.locateCenterOnScreen
        
        Args:
            screen: 屏幕截图 (PIL Image)
            template: 模板图片 (PIL Image)
            confidence: 置信度阈值
        
        Returns:
            MatchResult 或 None
        """
        if confidence is None:
            confidence = self.default_confidence
        
        # 使用 pyautogui.locateCenterOnScreen 进行匹配
        # 注意：需要传入模板图片路径或 Image 对象
        try:
            # pyautogui 直接在内存 Image 上工作
            location = pyautogui.locate(screen, template, confidence=confidence)
            
            if location:
                # location 是 (x, y, width, height) 元组
                x, y, w, h = location
                center_x, center_y = x + w // 2, y + h // 2
                return MatchResult(
                    x=center_x,
                    y=center_y,
                    width=w,
                    height=h,
                    confidence=confidence
                )
        except Exception as e:
            # pyautogui 可能抛出异常，返回 None
            pass
        
        return None
    
    def find_all_templates(
        self,
        screen: Image.Image,
        template: Image.Image,
        confidence: Optional[float] = None,
        max_results: int = 10
    ) -> List[MatchResult]:
        """
        查找所有匹配
        
        Args:
            screen: 屏幕截图
            template: 模板图片
            confidence: 置信度阈值
            max_results: 最大返回数
        
        Returns:
            MatchResult 列表
        """
        if confidence is None:
            confidence = self.default_confidence
        
        matches = []
        
        try:
            # 使用 locateAll 查找所有匹配
            locations = pyautogui.locateAll(screen, template, confidence=confidence)
            
            for i, location in enumerate(locations):
                if i >= max_results:
                    break
                x, y, w, h = location
                center_x, center_y = x + w // 2, y + h // 2
                matches.append(MatchResult(
                    x=center_x,
                    y=center_y,
                    width=w,
                    height=h,
                    confidence=confidence
                ))
        except Exception:
            pass
        
        return matches
    
    def template_exists(
        self,
        screen: Image.Image,
        template: Image.Image,
        confidence: Optional[float] = None
    ) -> bool:
        """
        检查模板是否存在
        
        Args:
            screen: 屏幕截图
            template: 模板图片
            confidence: 置信度阈值
        
        Returns:
            True/False
        """
        result = self.find_template(screen, template, confidence)
        return result is not None
    
    def locate_on_screen(self, template_path: str, confidence: float = 0.9) -> Optional[tuple]:
        """
        直接在屏幕上查找模板（便捷方法）
        
        Args:
            template_path: 模板图片路径
            confidence: 置信度阈值
        
        Returns:
            (x, y, width, height) 或 None
        """
        try:
            location = pyautogui.locateOnScreen(template_path, confidence=confidence)
            return location
        except Exception:
            return None
    
    def locate_center_on_screen(self, template_path: str, confidence: float = 0.9) -> Optional[tuple]:
        """
        在屏幕上查找模板并返回中心点（便捷方法）
        
        Args:
            template_path: 模板图片路径
            confidence: 置信度阈值
        
        Returns:
            (center_x, center_y) 或 None
        """
        try:
            location = pyautogui.locateCenterOnScreen(template_path, confidence=confidence)
            return location
        except Exception:
            return None
