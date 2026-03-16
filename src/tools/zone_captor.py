"""检测区域截图工具"""
import sys
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageGrab
from src.core.screen import ScreenManager, WindowInfo


class ZoneCaptor:
    """检测区域截图器"""
    
    def __init__(self):
        self.screen_manager = ScreenManager()
        self.current_window: Optional[WindowInfo] = None
    
    def find_window(self, title: str) -> Optional[WindowInfo]:
        """查找窗口"""
        return self.screen_manager.find_window(title)
    
    def capture_full_screen(self, output_path: str) -> str:
        """
        截取全屏
        
        Args:
            output_path: 输出路径
        
        Returns:
            保存的文件路径
        """
        screenshot = ImageGrab.grab()
        screenshot.save(output_path)
        return output_path
    
    def capture_window(self, window: WindowInfo, output_path: str) -> str:
        """
        截取窗口
        
        Args:
            window: 窗口信息
            output_path: 输出路径
        
        Returns:
            保存的文件路径
        """
        screenshot = ImageGrab.grab(bbox=(
            window.left, window.top,
            window.left + window.width,
            window.top + window.height
        ))
        screenshot.save(output_path)
        return output_path
    
    def capture_region(
        self,
        window: Optional[WindowInfo],
        x: int, y: int, w: int, h: int,
        output_path: str
    ) -> str:
        """
        截取区域
        
        Args:
            window: 窗口信息 (可选)
            x, y: 相对窗口左上角的坐标
            w, h: 区域宽高
            output_path: 输出路径
        
        Returns:
            保存的文件路径
        """
        if window:
            abs_x = window.left + x
            abs_y = window.top + y
        else:
            abs_x = x
            abs_y = y
        
        abs_x = max(0, abs_x)
        abs_y = max(0, abs_y)
        
        screenshot = ImageGrab.grab(bbox=(abs_x, abs_y, abs_x + w, abs_y + h))
        screenshot.save(output_path)
        return output_path
    
    def interactive_capture(self, window_title: str, output_dir: str) -> str:
        """
        交互式截图 (简化版本，打印说明)
        
        Args:
            window_title: 窗口标题
            output_dir: 输出目录
        
        Returns:
            保存的文件路径
        """
        print("=" * 50)
        print("检测区域截图工具")
        print("=" * 50)
        print()
        print("由于当前环境限制，请使用以下方式截图:")
        print()
        print("1. Windows 自带截图工具 (Win + Shift + S)")
        print("2. 或使用截图软件截取游戏窗口区域")
        print("3. 保存截图到指定目录")
        print()
        print(f"建议保存位置：{output_dir}/")
        print()
        print("或者使用 Python 代码截图:")
        print("""
from PIL import ImageGrab

# 截取全屏
screenshot = ImageGrab.grab()
screenshot.save("output.png")

# 截取区域 (x1, y1, x2, y2)
region = ImageGrab.grab(bbox=(100, 100, 300, 200))
region.save("region.png")
""")
        
        # 创建一个占位文件
        output_path = Path(output_dir) / "placeholder.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建一个示例图片
        img = Image.new('RGB', (200, 100), color='gray')
        img.save(str(output_path))
        
        return str(output_path)


# CLI 辅助函数
def capture_zone(output: str, window: Optional[str] = None):
    """CLI: 截图检测区域"""
    captor = ZoneCaptor()
    output_path = Path(output)
    output_dir = str(output_path.parent)
    
    if window:
        window_info = captor.find_window(window)
        if window_info:
            print(f"找到窗口：{window}")
            print(f"窗口尺寸：{window_info.width}x{window_info.height}")
            # 截取整个窗口作为示例
            captor.capture_window(window_info, str(output_path))
            print(f"截图已保存：{output_path}")
        else:
            print(f"未找到窗口：{window}")
            print("使用交互式截图...")
            captor.interactive_capture(window, output_dir)
    else:
        print("未指定窗口，截取全屏...")
        captor.capture_full_screen(str(output_path))
        print(f"截图已保存：{output_path}")
