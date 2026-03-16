"""屏幕捕捉和窗口管理模块"""
from dataclasses import dataclass
from typing import Optional, Tuple
from PIL import Image


@dataclass
class WindowInfo:
    """窗口信息"""
    title: str
    left: int
    top: int
    width: int
    height: int
    
    @property
    def right(self) -> int:
        return self.left + self.width
    
    @property
    def bottom(self) -> int:
        return self.top + self.height


class ScreenManager:
    """屏幕和窗口管理器"""
    
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """
        根据标题查找窗口
        
        Args:
            title: 窗口标题 (支持模糊匹配)
        
        Returns:
            WindowInfo 或 None
        """
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(title)
        
        if not windows:
            return None
        
        # 过滤过小的窗口（可能是任务栏图标或其他非主窗口）
        min_width = 200
        min_height = 100
        
        valid_windows = [
            w for w in windows 
            if w.width >= min_width and w.height >= min_height
        ]
        
        if not valid_windows:
            # 如果没有符合条件的，返回最大的窗口
            valid_windows = sorted(windows, key=lambda w: w.width * w.height, reverse=True)
        
        # 返回第一个有效的窗口
        window = valid_windows[0]
        return WindowInfo(
            title=window.title,
            left=window.left,
            top=window.top,
            width=window.width,
            height=window.height
        )
    
    def get_window_size(self, window: WindowInfo) -> Tuple[int, int]:
        """获取窗口尺寸"""
        return (window.width, window.height)
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取屏幕尺寸"""
        try:
            import screeninfo
            screens = screeninfo.get_monitors()
            if screens:
                return (screens[0].width, screens[0].height)
        except ImportError:
            pass
        return (1920, 1080)  # 默认
    
    def calculate_scale_factor(
        self,
        current_size: Tuple[int, int],
        reference_size: Tuple[int, int]
    ) -> float:
        """
        计算缩放因子
        
        Args:
            current_size: 当前窗口尺寸 (width, height)
            reference_size: 参考尺寸 (width, height)
        
        Returns:
            缩放因子 (0.0 - 1.0+)
        """
        curr_w, curr_h = current_size
        ref_w, ref_h = reference_size
        
        scale_x = curr_w / ref_w
        scale_y = curr_h / ref_h
        
        # 取较小值保证内容不超出
        return min(scale_x, scale_y)
    
    def get_screen_region(
        self,
        window: Optional[WindowInfo],
        x: int,
        y: int,
        w: int,
        h: int
    ) -> Image.Image:
        """
        截取屏幕区域
        
        Args:
            window: 窗口信息 (可选，如果不传则截取全屏)
            x, y: 相对窗口左上角的坐标
            w, h: 区域宽高
        
        Returns:
            PIL Image
        """
        from PIL import ImageGrab
        
        if window:
            # 截取窗口内的区域
            abs_x = window.left + x
            abs_y = window.top + y
        else:
            # 截取全屏区域
            abs_x = x
            abs_y = y
        
        # 确保坐标非负
        abs_x = max(0, abs_x)
        abs_y = max(0, abs_y)
        
        # 截取区域
        screenshot = ImageGrab.grab(bbox=(abs_x, abs_y, abs_x + w, abs_y + h))
        return screenshot
    
    def auto_detect_scale_factor(
        self,
        window_title: str,
        reference_resolution: Tuple[int, int] = (1920, 1080)
    ) -> Optional[float]:
        """
        自动检测缩放因子
        
        Args:
            window_title: 窗口标题
            reference_resolution: 参考分辨率
        
        Returns:
            缩放因子或 None (窗口未找到)
        """
        window = self.find_window(window_title)
        if not window:
            return None
        
        current_size = self.get_window_size(window)
        return self.calculate_scale_factor(current_size, reference_resolution)
