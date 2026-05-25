"""color 模式 - alpha 通道颜色提取监测"""
from pathlib import Path
from typing import Tuple, Optional, Any
import logging
import math

import pyautogui
from PIL import Image
import numpy as np


class ColorMonitorStrategy:
    """color 模式：基于 alpha 通道提取颜色对比"""

    def __init__(self):
        self._logger = logging.getLogger("monitor.color")

    def detect(
        self,
        screenshot,
        normal_path: Path,
        **kwargs
    ) -> Tuple[str, Optional[Tuple[int, int]], Optional[tuple]]:
        """检测图标状态

        使用去背景模板的 alpha 通道作为 mask，提取截图对应区域的真实颜色

        Returns:
            (state, coordinates, avg_color)
            - avg_color: (R, G, B) 平均颜色
        """
        normal_location = None
        try:
            normal_location = pyautogui.locate(
                str(normal_path), screenshot, confidence=0.8
            )
        except Exception as e:
            self._logger.debug(f"[监测-color] normal 定位失败: {e}")

        if not normal_location:
            self._logger.info("[监测-color] 未定位到 normal 图标")
            return "none", None, None

        x, y, w, h = normal_location
        center_x, center_y = x + w // 2, y + h // 2
        sub_img = screenshot.crop((x, y, x + w, y + h))

        self._logger.info(
            f"[监测-color] 定位到图标: ({x},{y},{w},{h}), "
            f"center=({center_x},{center_y}), 尺寸={sub_img.size}",
        )

        avg_color = self._extract_color_with_mask(sub_img, normal_path)
        if avg_color is None:
            self._logger.error("[监测-color] 颜色提取失败")
            return "none", None, None

        self._logger.info(
            f"[监测-color] 当前平均颜色: {avg_color}",
        )

        return "normal", (center_x, center_y), avg_color

    def _extract_color_with_mask(
        self, sub_img: Image.Image, template_path: Path
    ) -> Optional[tuple]:
        """使用模板 alpha 通道作为 mask 提取颜色

        Args:
            sub_img: 截图子图
            template_path: 模板图片路径（带 alpha 通道）

        Returns:
            (R, G, B) 平均颜色
        """
        try:
            template = Image.open(str(template_path))

            if template.mode != "RGBA":
                template = template.convert("RGBA")
            if sub_img.mode != "RGBA":
                sub_img = sub_img.convert("RGBA")

            template_np = np.array(template)
            sub_np = np.array(sub_img)

            if template_np.shape[:2] != sub_np.shape[:2]:
                template_np = np.array(
                    template.resize(sub_img.size, Image.Resampling.LANCZOS)
                )

            alpha_mask = template_np[:, :, 3]

            valid_mask = alpha_mask > 0

            if not np.any(valid_mask):
                self._logger.warning("[监测-color] 模板无有效 alpha 区域")
                return None

            valid_pixels = sub_np[valid_mask]

            if len(valid_pixels) == 0:
                return None

            avg_color = valid_pixels[:, :3].mean(axis=0)

            return tuple(int(c) for c in avg_color)

        except Exception as e:
            self._logger.error(f"[监测-color] 颜色提取异常: {e}")
            return None

    @staticmethod
    def compute_color_diff(color1: tuple, color2: tuple) -> float:
        """计算两个颜色的差异（归一化到 0-1）

        Args:
            color1: (R, G, B)
            color2: (R, G, B)

        Returns:
            0-1 差异值
        """
        diff = math.sqrt(
            (color1[0] - color2[0]) ** 2
            + (color1[1] - color2[1]) ** 2
            + (color1[2] - color2[2]) ** 2
        )
        return diff / 441.67  # 归一化