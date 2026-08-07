"""图像识别模块 - 使用 pyautogui 进行模板匹配"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import numpy as np
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
    screen_x: Optional[int] = None
    screen_y: Optional[int] = None

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
        if path in self._template_cache:
            return self._template_cache[path]

        if not Path(path).exists():
            return None

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
        confidence: Optional[float] = None,
    ) -> Optional[MatchResult]:
        """在屏幕图像中查找模板"""
        if confidence is None:
            confidence = self.default_confidence

        try:
            location = pyautogui.locate(screen, template, confidence=confidence)

            if location:
                x, y, w, h = location
                center_x, center_y = x + w // 2, y + h // 2
                return MatchResult(
                    x=center_x, y=center_y, width=w, height=h, confidence=confidence
                )
        except Exception:
            pass

        return None

    def find_in_region(
        self,
        screen: Image.Image,
        template: Union[str, Path, Image.Image],
        region: dict,
        confidence: Optional[float] = None,
        grayscale: bool = False,
    ) -> List[MatchResult]:
        """在指定百分比区域内查找模板

        Args:
            screen: 屏幕截图 (PIL Image)
            template: 模板图片（路径或 PIL Image）
            region: 百分比区域 {"x": (x1, x2), "y": (y1, y2)}，范围 0-1
            confidence: 置信度
            grayscale: 是否灰度匹配

        Returns:
            匹配结果列表（绝对屏幕坐标在 screen_x/screen_y）
        """
        if confidence is None:
            confidence = self.default_confidence

        screen_w, screen_h = screen.size
        x1 = round(region["x"][0] * screen_w)
        y1 = round(region["y"][0] * screen_h)
        x2 = round(region["x"][1] * screen_w)
        y2 = round(region["y"][1] * screen_h)
        return self._match_in_region(
            screen, template, x1, y1, x2, y2, confidence, grayscale
        )

    def find_in_abs_region(
        self,
        screen: Image.Image,
        template: Union[str, Path, Image.Image],
        center: Tuple[int, int],
        size: Tuple[int, int],
        confidence: Optional[float] = None,
        grayscale: bool = False,
    ) -> List[MatchResult]:
        """在指定中心点+尺寸区域内查找模板

        Args:
            screen: 屏幕截图 (PIL Image)
            template: 模板图片（路径或 PIL Image）
            center: 区域中心点 (x, y) 绝对像素
            size: 区域尺寸 (w, h) 绝对像素
            confidence: 置信度
            grayscale: 是否灰度匹配

        Returns:
            匹配结果列表
        """
        if confidence is None:
            confidence = self.default_confidence

        cx, cy = center
        w, h = size
        x1 = cx - w // 2
        y1 = cy - h // 2
        x2 = x1 + w
        y2 = y1 + h
        return self._match_in_region(
            screen, template, x1, y1, x2, y2, confidence, grayscale
        )

    def _match_in_region(
        self,
        screen: Image.Image,
        template,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        confidence: float,
        grayscale: bool,
    ) -> List[MatchResult]:
        """区域匹配核心 - cv2 模板匹配"""
        tpl = self._load_template_image(template)
        if tpl is None:
            return []

        screen_w, screen_h = screen.size
        x1 = max(0, min(x1, screen_w))
        y1 = max(0, min(y1, screen_h))
        x2 = max(x1, min(x2, screen_w))
        y2 = max(y1, min(y2, screen_h))

        screen_rgb = np.asarray(screen.convert("RGB"))
        tpl_rgb = np.asarray(tpl.convert("RGB"))
        if grayscale:
            screen_arr = cv2.cvtColor(screen_rgb, cv2.COLOR_RGB2GRAY)
            tpl_arr = cv2.cvtColor(tpl_rgb, cv2.COLOR_RGB2GRAY)
        else:
            screen_arr = cv2.cvtColor(screen_rgb, cv2.COLOR_RGB2BGR)
            tpl_arr = cv2.cvtColor(tpl_rgb, cv2.COLOR_RGB2BGR)

        th, tw = tpl_arr.shape[:2]
        crop_w = x2 - x1
        crop_h = y2 - y1
        if crop_w < tw or crop_h < th:
            return []

        crop = screen_arr[y1:y2, x1:x2]
        result = cv2.matchTemplate(crop, tpl_arr, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < confidence:
            return []

        m_x = x1 + max_loc[0]
        m_y = y1 + max_loc[1]
        center_x = m_x + tw // 2
        center_y = m_y + th // 2
        return [
            MatchResult(
                x=center_x - x1,
                y=center_y - y1,
                width=tw,
                height=th,
                confidence=confidence,
                screen_x=center_x,
                screen_y=center_y,
            )
        ]

    def _load_template_image(self, template) -> Optional[Image.Image]:
        """统一模板入参：路径字符串或 PIL Image"""
        if isinstance(template, (str, Path)):
            return self.load_template(str(template))
        return template

    def locate_on_screen(
        self, template_path: str, confidence: float = 0.9
    ) -> Optional[tuple]:
        """直接在屏幕上查找模板"""
        try:
            location = pyautogui.locateOnScreen(template_path, confidence=confidence)
            return location
        except Exception:
            return None

    def locate_center_on_screen(
        self, template_path: str, confidence: float = 0.9
    ) -> Optional[tuple]:
        """在屏幕上查找模板并返回中心点"""
        try:
            location = pyautogui.locateCenterOnScreen(
                template_path, confidence=confidence
            )
            return location
        except Exception:
            return None

    @staticmethod
    def compute_histogram(image: Image.Image, bins: int = 32) -> Optional[np.ndarray]:
        """计算 BGR 三通道直方图并归一化

        Args:
            image: PIL Image
            bins: 每通道直方图 bin 数

        Returns:
            归一化直方图数组 (3*bins,) 或 None
        """
        try:
            arr = np.array(image.convert("RGB"))
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            hist = np.zeros((3, bins), dtype=np.float32)
            for ch in range(3):
                h = cv2.calcHist([bgr], [ch], None, [bins], [0, 256])
                cv2.normalize(h, h)
                hist[ch] = h.flatten()
            return hist.flatten()
        except Exception:
            return None

    def compare_histogram(self, img1: Image.Image, img2: Image.Image) -> float:
        """比较两张图片直方图相似度

        Args:
            img1: PIL Image
            img2: PIL Image

        Returns:
            0-1 相似度，1 表示完全相同
        """
        h1 = self.compute_histogram(img1)
        h2 = self.compute_histogram(img2)
        if h1 is None or h2 is None:
            raise ValueError("Failed to compute histogram for one or both images")
        return float(cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL))

    def match_template_confidence(
        self, screen: Image.Image, template: Image.Image
    ) -> float:
        """计算模板匹配的置信度

        Args:
            screen: 屏幕截图
            template: 模板图片

        Returns:
            0-1 置信度
        """
        try:
            screen_cv = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            template_cv = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)

            result = cv2.matchTemplate(screen_cv, template_cv, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            return float(max_val)
        except Exception:
            return 0.0
