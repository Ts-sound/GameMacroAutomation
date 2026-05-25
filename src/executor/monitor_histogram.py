"""histogram 模式 - 直方图对比监测"""
from pathlib import Path
from typing import Tuple, Optional, Any, List
import logging

import pyautogui
from PIL import Image

from src.core.image import ImageMatcher


class HistogramMonitorStrategy:
    """histogram 模式：基于直方图相似度对比"""

    def __init__(self):
        self.image_matcher = ImageMatcher()
        self._logger = logging.getLogger("monitor.histogram")

    def detect(
        self,
        screenshot,
        normal_path: Path,
        region: dict = None,
        changed_template: List[str] = None,
        changed_paths: List[Path] = None,
        histogram_threshold: float = 0.7,
        **kwargs
    ) -> Tuple[str, Optional[Tuple[int, int]], Optional[Any]]:
        """检测图标状态

        Returns:
            (state, coordinates, extra_data)
        """
        changed_template = changed_template or []
        changed_paths = changed_paths or []

        normal_location = None
        try:
            normal_location = pyautogui.locate(
                str(normal_path), screenshot, confidence=0.8
            )
        except Exception as e:
            self._logger.debug(f"[监测-hist] normal 定位失败: {e}")

        if normal_location:
            x, y, w, h = normal_location
            center_x, center_y = x + w // 2, y + h // 2
            sub_img = screenshot.crop((x, y, x + w, y + h))
            self._logger.info(
                f"[监测-hist] 定位到 normal 图标: ({x},{y},{w},{h}), "
                f"center=({center_x},{center_y}), 尺寸={sub_img.size}",
            )

            normal_img = Image.open(str(normal_path)).convert("RGB")
            normal_img = normal_img.resize(
                sub_img.size, Image.Resampling.LANCZOS
            )

            try:
                similarity = self.image_matcher.compare_histogram(
                    sub_img, normal_img
                )
            except ValueError as e:
                self._logger.error(
                    f"[监测-hist] normal 直方图计算失败: {e}"
                )
                return "none", None, None

            self._logger.info(
                f"[监测-hist] normal 相似度: {similarity:.4f} "
                f"(阈值={histogram_threshold})",
            )

            if similarity > histogram_threshold:
                self._logger.info(
                    "[监测-hist] 检测到 normal 图标（颜色匹配）"
                )
                return "normal", (center_x, center_y), None

        for tpl, tpl_path in zip(changed_template, changed_paths):
            changed_location = None
            try:
                changed_location = pyautogui.locate(
                    str(tpl_path), screenshot, confidence=0.8
                )
            except Exception as e:
                self._logger.debug(f"[监测-hist] {tpl} 定位失败: {e}")

            if changed_location:
                x, y, w, h = changed_location
                center_x, center_y = x + w // 2, y + h // 2
                sub_img = screenshot.crop((x, y, x + w, y + h))
                self._logger.info(
                    f"[监测-hist] 定位到 changed 图标 ({tpl}): "
                    f"({x},{y},{w},{h}), center=({center_x},{center_y})",
                )

                changed_img = Image.open(str(tpl_path)).convert("RGB")
                changed_img = changed_img.resize(
                    sub_img.size, Image.Resampling.LANCZOS
                )

                try:
                    sim = self.image_matcher.compare_histogram(
                        sub_img, changed_img
                    )
                except ValueError as e:
                    self._logger.error(
                        f"[监测-hist] changed 直方图计算失败 ({tpl}): {e}"
                    )
                    continue

                self._logger.info(
                    f"[监测-hist] changed ({tpl}) 相似度: {sim:.4f} "
                    f"(阈值={histogram_threshold})",
                )

                if sim > histogram_threshold:
                    self._logger.info(
                        f"[监测-hist] 检测到 changed 图标 ({tpl})"
                    )
                    return "changed", (center_x, center_y), None

        self._logger.info("[监测-hist] 未定位到任何图标")
        return "none", None, None