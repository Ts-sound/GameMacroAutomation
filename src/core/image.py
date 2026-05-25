"""图像识别模块 - 使用 pyautogui 进行模板匹配"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

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
        template_path: str,
        region: dict,
        confidence: Optional[float] = None,
    ) -> List[MatchResult]:
        """在指定区域内查找模板"""
        if confidence is None:
            confidence = self.default_confidence

        # 直接使用截图的尺寸，而不是通过 get_screen_by_id
        screen_w, screen_h = screen.size

        x_start, x_end = region["x"]
        y_start, y_end = region["y"]

        abs_x = round(x_start * screen_w)
        abs_y = round(y_start * screen_h)
        abs_w = round((x_end - x_start) * screen_w)
        abs_h = round((y_end - y_start) * screen_h)

        print(
            f"DEBUG find_in_region: screen={screen.size}, region={region}, abs=({abs_x},{abs_y},{abs_w},{abs_h})"
        )

        matches: List[MatchResult] = []

        try:
            location = pyautogui.locateOnScreen(template_path, confidence=confidence)

            if location:
                x, y, w, h = location
                center_x, center_y = x + w // 2, y + h // 2

                in_region = (
                    abs_x <= center_x < abs_x + abs_w
                    and abs_y <= center_y < abs_y + abs_h
                )

                print(
                    f"DEBUG: 找到点 ({center_x}, {center_y}), 区域 ({abs_x},{abs_y})-({abs_x+abs_w},{abs_y+abs_h}), in_region={in_region}"
                )

                if in_region:
                    matches.append(
                        MatchResult(
                            x=center_x - abs_x,
                            y=center_y - abs_y,
                            width=w,
                            height=h,
                            confidence=confidence,
                            screen_x=center_x,
                            screen_y=center_y,
                        )
                    )
        except Exception as e:
            print(f"DEBUG: 检测异常: {e}")

        return matches

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
