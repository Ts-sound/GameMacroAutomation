"""录制器模块 - 录制输入并生成 YAML 脚本"""
import time
import yaml
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from PIL import Image

from src.core.screen import ScreenManager, WindowInfo
from src.core.input import InputRecorder, RecordedAction
from src.core.config import MacroScript, ScriptMeta, ScriptConfig, ScriptAssets


class ScriptRecorder:
    """脚本录制器"""
    
    def __init__(self, output_dir: str = "scripts"):
        """
        Args:
            output_dir: 脚本输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 图片保存目录（与脚本同目录下的 images 文件夹）
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        self.screen_manager = ScreenManager()
        self.input_recorder: Optional[InputRecorder] = None
        self.current_window: Optional[WindowInfo] = None
        
        # 截图配置
        self.screenshot_size = 100  # 截取点击位置周围 100x100 区域
        self.click_counter = 0  # 点击计数器，用于生成唯一文件名
    
    def find_game_window(self, title: str) -> Optional[WindowInfo]:
        """查找游戏窗口"""
        return self.screen_manager.find_window(title)
    
    def start_recording(self, window_title: str) -> bool:
        """开始录制"""
        self.current_window = self.find_game_window(window_title)
        if not self.current_window:
            print(f"未找到窗口：{window_title}")
            return False
        
        self.click_counter = 0
        self.input_recorder = InputRecorder(self.screen_manager)
        self.input_recorder.start_recording()
        return True
    
    def stop_recording(self) -> List[RecordedAction]:
        """停止录制"""
        if not self.input_recorder:
            return []
        return self.input_recorder.stop_recording()
    
    def capture_click_region(self, x: int, y: int) -> Optional[str]:
        """
        截取点击位置周围的区域
        
        Args:
            x, y: 屏幕绝对坐标
        
        Returns:
            保存的图片文件名，失败返回 None
        """
        if not self.current_window:
            return None
        
        # 重新获取窗口位置（窗口可能被移动）
        current_window = self.screen_manager.find_window(self.current_window.title)
        if not current_window:
            print(f"警告：窗口 {self.current_window.title} 已关闭")
            return None
        
        # 计算相对窗口坐标
        rel_x = x - current_window.left
        rel_y = y - current_window.top
        
        # 检查坐标是否在窗口内
        if (rel_x < 0 or rel_x >= current_window.width or
            rel_y < 0 or rel_y >= current_window.height):
            print(f"警告：点击位置 ({x}, {y}) 超出窗口范围 (窗口：{current_window.left},{current_window.top} {current_window.width}x{current_window.height})")
            # 仍然尝试截图，使用屏幕坐标
            return self._capture_screen_region(x, y)
        
        # 计算截图区域（以点击点为中心）
        half_size = self.screenshot_size // 2
        x1 = max(0, rel_x - half_size)
        y1 = max(0, rel_y - half_size)
        x2 = min(current_window.width, x1 + self.screenshot_size)
        y2 = min(current_window.height, y1 + self.screenshot_size)
        
        # 调整 x1, y1 确保截图尺寸为 screenshot_size x screenshot_size
        if x2 - x1 < self.screenshot_size:
            x1 = max(0, x2 - self.screenshot_size)
        if y2 - y1 < self.screenshot_size:
            y1 = max(0, y2 - self.screenshot_size)
        
        # 截图（窗口内区域）
        screenshot = self.screen_manager.get_screen_region(
            current_window, x1, y1, x2 - x1, y2 - y1
        )
        
        # 保存截图
        self.click_counter += 1
        filename = f"click_{self.click_counter:03d}.png"
        filepath = self.images_dir / filename
        screenshot.save(str(filepath))
        
        return filename
    
    def _capture_screen_region(self, x: int, y: int) -> Optional[str]:
        """
        截取屏幕区域（当点击超出窗口时使用）
        
        Args:
            x, y: 屏幕绝对坐标
        
        Returns:
            保存的图片文件名
        """
        half_size = self.screenshot_size // 2
        x1 = max(0, x - half_size)
        y1 = max(0, y - half_size)
        
        # 直接截取屏幕区域
        from PIL import ImageGrab
        screenshot = ImageGrab.grab(bbox=(x1, y1, x1 + self.screenshot_size, y1 + self.screenshot_size))
        
        self.click_counter += 1
        filename = f"click_{self.click_counter:03d}.png"
        filepath = self.images_dir / filename
        screenshot.save(str(filepath))
        
        return filename
    
    def actions_to_yaml(
        self,
        actions: List[RecordedAction],
        window_title: str,
        image_map: Optional[dict] = None
    ) -> dict:
        """
        将动作列表转换为 YAML 结构
        
        Args:
            actions: 录制的动作列表
            window_title: 窗口标题
            image_map: 动作索引到图片文件名的映射
        
        Returns:
            YAML 字典结构
        """
        image_map = image_map or {}
        
        # 构建动作序列
        yaml_actions = []
        assets_images = {}
        
        for i, action in enumerate(actions):
            if action.action_type == "mouse_click":
                # 检查是否有对应的截图
                if i in image_map:
                    img_name = f"click_{i+1}"
                    img_file = image_map[i]
                    assets_images[img_name] = f"images/{img_file}"
                    
                    # 计算相对窗口的偏移
                    if self.current_window:
                        offset_x = action.x - self.current_window.left
                        offset_y = action.y - self.current_window.top
                    else:
                        offset_x = action.x
                        offset_y = action.y
                    
                    yaml_actions.append({
                        "type": "click_image",
                        "image": img_name,
                        "offset": [offset_x % self.screenshot_size, offset_y % self.screenshot_size]
                    })
                else:
                    # 没有截图，使用普通点击
                    yaml_actions.append({
                        "type": "click",
                        "x": action.x,
                        "y": action.y,
                        "button": action.button
                    })
                    
            elif action.action_type == "key_press":
                if action.key:  # 忽略空按键
                    yaml_actions.append({
                        "type": "keypress",
                        "key": action.key
                    })
        
        # 添加时间间隔
        if len(actions) > 1:
            enhanced_actions = []
            for i, action in enumerate(yaml_actions):
                if i > 0:
                    # 找到对应的原始动作索引
                    orig_idx = i
                    delay_ms = actions[orig_idx].timestamp - actions[orig_idx - 1].timestamp
                    if delay_ms > 50:  # 大于 50ms 才添加 delay
                        enhanced_actions.append({"type": "delay", "ms": delay_ms})
                enhanced_actions.append(action)
            yaml_actions = enhanced_actions
        
        return {
            "meta": {
                "name": "录制脚本",
                "version": "1.0",
                "created_by": "recorder"
            },
            "config": {
                "window_title": window_title,
                "log_level": "INFO",
                "retry_times": 3
            },
            "assets": {
                "images": assets_images
            },
            "actions": yaml_actions
        }
    
    def save_script(self, yaml_data: dict, script_name: str) -> str:
        """保存脚本到文件"""
        script_path = self.output_dir / f"{script_name}.yaml"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)
        
        return str(script_path)
    
    def record(self, window_title: str, output_name: str) -> str:
        """
        完整录制流程
        
        Args:
            window_title: 游戏窗口标题
            output_name: 输出脚本名称
        
        Returns:
            保存的文件路径
        """
        print(f"开始录制，窗口：{window_title}")
        print("按 Ctrl+C 停止录制...")
        
        if not self.start_recording(window_title):
            raise RuntimeError(f"无法找到窗口：{window_title}")
        
        print("录制中... 每次点击会自动截图")
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        
        actions = self.stop_recording()
        print(f"\n录制完成，共 {len(actions)} 个动作")
        
        # 处理点击截图
        image_map = {}
        for i, action in enumerate(actions):
            if action.action_type == "mouse_click":
                img_file = self.capture_click_region(action.x, action.y)
                if img_file:
                    image_map[i] = img_file
                    print(f"  点击 {i+1}: 已截图 {img_file}")
        
        yaml_data = self.actions_to_yaml(actions, window_title, image_map)
        script_path = self.save_script(yaml_data, output_name)
        
        print(f"\n脚本已保存：{script_path}")
        print(f"图片已保存：{self.images_dir}")
        return script_path


# CLI 辅助函数
def list_windows():
    """CLI: 列出所有可用窗口"""
    import pygetwindow as gw
    
    windows = gw.getAllWindows()
    
    # 过滤空标题和过小的窗口
    valid_windows = [
        w for w in windows 
        if w.title and w.width > 100 and w.height > 100
    ]
    
    # 按标题排序
    valid_windows.sort(key=lambda w: w.title.lower())
    
    print("\n" + "=" * 60)
    print("可用窗口列表")
    print("=" * 60)
    print()
    
    if not valid_windows:
        print("未找到符合条件的窗口")
        print("提示：最小窗口尺寸为 100x100")
    else:
        print(f"找到 {len(valid_windows)} 个窗口:\n")
        
        for i, w in enumerate(valid_windows, 1):
            print(f"  [{i:3d}] {w.title}")
            print(f"        位置：({w.left}, {w.top})  尺寸：{w.width}x{w.height}")
    
    print()
    print("=" * 60)
    print()
    print("使用示例:")
    print('  python -m src.main record -o scripts/test.yaml -w "窗口标题"')
    print()
    print("或者使用窗口编号 (1-{0}):".format(len(valid_windows)))
    print("  python -m src.main record -o scripts/test.yaml -w 1")
    print()


def record_script(output: str, window: Optional[str] = None):
    """CLI: 录制脚本"""
    if not window:
        list_windows()
        return
    
    # 支持数字索引选择窗口
    if window.isdigit():
        import pygetwindow as gw
        windows = [w for w in gw.getAllWindows() if w.title and w.width > 100 and w.height > 100]
        windows.sort(key=lambda w: w.title.lower())
        
        idx = int(window) - 1
        if 0 <= idx < len(windows):
            window = windows[idx].title
        else:
            print(f"错误：窗口编号 {window} 超出范围 (1-{len(windows)})")
            return
    
    recorder = ScriptRecorder()
    output_name = Path(output).stem
    output_dir = str(Path(output).parent)
    recorder.output_dir = Path(output_dir)
    recorder.images_dir = Path(output_dir) / "images"
    recorder.images_dir.mkdir(parents=True, exist_ok=True)
    
    recorder.record(window, output_name)
