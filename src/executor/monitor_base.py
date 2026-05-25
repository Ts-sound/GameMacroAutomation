"""图标状态监测策略基类"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Optional, Any


class MonitorStrategy(ABC):
    """图标状态监测策略基类"""

    @abstractmethod
    def detect(
        self,
        screenshot,
        normal_path: Path,
        **kwargs
    ) -> Tuple[str, Optional[Tuple[int, int]], Optional[Any]]:
        """检测图标状态

        Args:
            screenshot: PIL Image 截图
            normal_path: 正常态模板图片路径
            **kwargs: 额外参数

        Returns:
            (state, coordinates, extra_data)
            - state: "none" | "normal" | "changed"
            - coordinates: (x, y) 全屏坐标或 None
            - extra_data: 额外数据（如 color 模式的 avg_color）
        """
        pass

    def log(self, message: str, level: str = "INFO"):
        """日志输出（子类可覆盖）"""
        import logging
        logger = logging.getLogger("monitor")
        getattr(logger, level.lower())(message)