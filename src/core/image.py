"""图像识别模块 - OpenCV 模板匹配"""
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
import cv2
import numpy as np
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
    """图像匹配器"""
    
    def __init__(self, default_confidence: float = 0.8):
        """
        Args:
            default_confidence: 默认匹配置信度阈值
        """
        self.default_confidence = default_confidence
        self._template_cache: dict[str, np.ndarray] = {}
    
    def load_template(self, path: str) -> Optional[np.ndarray]:
        """
        加载模板图片
        
        Args:
            path: 图片路径
        
        Returns:
            OpenCV numpy 数组或 None
        """
        # 检查缓存
        if path in self._template_cache:
            return self._template_cache[path]
        
        # 加载图片
        if not Path(path).exists():
            return None
        
        # PIL 转 OpenCV
        pil_img = Image.open(path)
        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        # 缓存
        self._template_cache[path] = cv_img
        return cv_img
    
    def clear_cache(self):
        """清除模板缓存"""
        self._template_cache.clear()
    
    def find_template(
        self,
        screen: Image.Image,
        template: np.ndarray,
        confidence: Optional[float] = None
    ) -> Optional[MatchResult]:
        """
        在屏幕图像中查找模板
        
        Args:
            screen: 屏幕截图 (PIL Image)
            template: 模板图片 (OpenCV numpy)
            confidence: 置信度阈值
        
        Returns:
            MatchResult 或 None
        """
        if confidence is None:
            confidence = self.default_confidence
        
        # 检查模板尺寸是否小于截图
        if template.shape[0] > screen.height or template.shape[1] > screen.width:
            # 模板比截图大，缩小模板
            scale = min(screen.width / template.shape[1], screen.height / template.shape[0])
            new_width = int(template.shape[1] * scale * 0.9)  # 90% 保证小于截图
            new_height = int(template.shape[0] * scale * 0.9)
            template = cv2.resize(template, (new_width, new_height))
        
        # 转屏幕为 OpenCV
        screen_cv = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        
        # 模板匹配
        result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # 检查置信度
        if max_val >= confidence:
            h, w = template.shape[:2]
            return MatchResult(
                x=int(max_loc[0]),
                y=int(max_loc[1]),
                width=w,
                height=h,
                confidence=float(max_val)
            )
        
        return None
    
    def find_all_templates(
        self,
        screen: Image.Image,
        template: np.ndarray,
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
        
        screen_cv = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
        
        matches = []
        h, w = template.shape[:2]
        
        # 找到所有超过阈值的匹配
        locations = np.where(result >= confidence)
        
        for pt in zip(*locations[::-1]):
            matches.append(MatchResult(
                x=int(pt[0]),
                y=int(pt[1]),
                width=w,
                height=h,
                confidence=float(result[pt[1], pt[0]])
            ))
            
            if len(matches) >= max_results:
                break
        
        # 按置信度排序
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches
    
    def template_exists(
        self,
        screen: Image.Image,
        template: np.ndarray,
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
