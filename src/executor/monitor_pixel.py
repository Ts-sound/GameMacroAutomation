"""pixel/template 模式 - 模板匹配监测"""
from pathlib import Path
from typing import Tuple, Optional, Any, List
import logging

import pyautogui

from src.core.image import ImageMatcher


class PixelMonitorStrategy:
    """pixel/template 模式：基于 pyautogui 模板匹配"""

    def __init__(self):
        self.image_matcher = ImageMatcher()
        self._logger = logging.getLogger("monitor.pixel")

    def detect(
        self,
        screenshot,
        normal_path: Path,
        region: dict = None,
        changed_template: List[str] = None,
        changed_paths: List[Path] = None,
        **kwargs
    ) -> Tuple[str, Optional[Tuple[int, int]], Optional[Any]]:
        """检测图标状态

        Returns:
            (state, coordinates, extra_data)
        """
        changed_template = changed_template or []
        changed_paths = changed_paths or []

        self._logger.info(f"[监测-pixel] 截图尺寸: {screenshot.size}")

        try:
            loc = pyautogui.locateCenterOnScreen(
                str(normal_path), confidence=0.8
            )
            self._logger.info(f"[监测-pixel] pyautogui 直接检测: {loc}")
        except Exception as e:
            self._logger.debug(f"[监测-pixel] pyautogui 检测失败: {e}")

        normal_matches = self.image_matcher.find_in_region(
            screenshot,
            str(normal_path),
            region or {"x": (0.0, 1.0), "y": (0.0, 1.0)},
            confidence=0.8,
        )

        changed_matches = []
        matched_template = None
        for tpl, tpl_path in zip(changed_template, changed_paths):
            matches = self.image_matcher.find_in_region(
                screenshot,
                str(tpl_path),
                region or {"x": (0.0, 1.0), "y": (0.0, 1.0)},
                confidence=0.8,
            )
            if matches:
                changed_matches = matches
                matched_template = tpl
                break

        match_info = (
            f"[监测-pixel] 匹配结果 - normal: {len(normal_matches)}, "
            f"changed: {len(changed_matches)}"
        )
        if matched_template:
            match_info += f" (matched: {matched_template})"
        self._logger.info(match_info)

        if normal_matches:
            normal_conf = self._get_confidence(screenshot, normal_path)
            self._logger.info(
                f"[监测-pixel] 检测到 normal 图标，位置: "
                f"({normal_matches[0].screen_x}, {normal_matches[0].screen_y}), "
                f"置信度: {normal_conf:.4f}",
            )
            return "normal", (
                normal_matches[0].screen_x,
                normal_matches[0].screen_y,
            ), None
        elif changed_matches:
            changed_conf = self._get_confidence(
                screenshot, changed_paths[changed_template.index(matched_template)]
            ) if matched_template else 0.0
            self._logger.info(
                f"[监测-pixel] 检测到 changed 图标 ({matched_template})，"
                f"位置: ({changed_matches[0].screen_x}, "
                f"{changed_matches[0].screen_y}), 置信度: {changed_conf:.4f}",
            )
            return "changed", (
                changed_matches[0].screen_x,
                changed_matches[0].screen_y,
            ), None
        else:
            self._logger.info("[监测-pixel] 未检测到任何图标")
            return "none", None, None

    def _get_confidence(self, screenshot, template_path) -> float:
        """计算模板匹配置信度"""
        try:
            template = self.image_matcher.load_template(str(template_path))
            if template:
                return self.image_matcher.match_template_confidence(
                    screenshot, template
                )
        except Exception:
            pass
        return 0.0