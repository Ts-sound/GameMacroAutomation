"""输入控制模块 - 封装 pyautogui 和 pynput"""
import time
import math
import random
import logging
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum

import pyautogui
from pynput import mouse, keyboard


class MouseButton(Enum):
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


@dataclass
class RecordedAction:
    """录制的动作"""
    timestamp: int  # 相对时间 ms
    action_type: str  # mouse_click, key_press, mouse_move
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None
    key: Optional[str] = None
    window_title: Optional[str] = None


@dataclass
class MouseStats:
    """鼠标移动统计"""
    total_distance: float = 0.0
    total_duration: float = 0.0
    move_count: int = 0
    
    @property
    def avg_speed(self) -> float:
        """平均速度 (pixels/ms)"""
        if self.total_duration <= 0:
            return 0.0
        return self.total_distance / self.total_duration
    
    @property
    def avg_speed_pixels_per_second(self) -> float:
        """平均速度 (pixels/second)"""
        return self.avg_speed * 1000


class InputController:
    """输入控制器 - 执行动作"""
    
    def __init__(self, scale_factor: float = 1.0, logger: Optional[logging.Logger] = None):
        """
        Args:
            scale_factor: 坐标缩放因子
            logger: 日志记录器
        """
        self.scale_factor = scale_factor
        self._logger = logger
        self.stats = MouseStats()
        
        # 鼠标移动配置
        self.min_move_duration = 0.1  # 最小移动时间 (秒)
        self.max_move_duration = 0.5  # 最大移动时间 (秒)
        self.humanize_factor = 0.2    # 人类行为模拟因子 (20% 随机性)
        
        # 配置 pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01  # 降低默认延迟
    
    def _calculate_move_duration(self, distance: float) -> float:
        """
        计算鼠标移动时长（模拟人类行为）
        
        Args:
            distance: 移动距离 (pixels)
        
        Returns:
            移动时长 (秒)
        """
        # 基于距离计算基础时长 (假设平均速度 1500 pixels/second)
        base_duration = distance / 1500.0
        
        # 限制在最小/最大范围内
        base_duration = max(self.min_move_duration, min(self.max_move_duration, base_duration))
        
        # 添加随机性模拟人类行为
        random_factor = 1.0 + random.uniform(-self.humanize_factor, self.humanize_factor)
        
        return base_duration * random_factor
    
    def _calculate_distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """计算两点间距离"""
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def scale_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """应用缩放因子到坐标"""
        scaled_x = int(x * self.scale_factor)
        scaled_y = int(y * self.scale_factor)
        return (scaled_x, scaled_y)
    
    def click(self, x: int, y: int, button: str = 'left'):
        """
        点击指定坐标
        
        Args:
            x, y: 坐标 (自动应用缩放)
            button: 'left', 'right', 'middle'
        """
        scaled_x, scaled_y = self.scale_coordinates(x, y)
        pyautogui.click(x=scaled_x, y=scaled_y, button=button)
        
        if self._logger:
            self._logger.debug(f"[输入] 点击：({x},{y}) -> 缩放后 ({scaled_x},{scaled_y})")
    
    def click_with_move(self, x: int, y: int, button: str = 'left', apply_scale: bool = True):
        """
        移动到目标位置后点击（模拟真实鼠标行为）
        
        Args:
            x, y: 目标坐标
            button: 鼠标按钮
            apply_scale: 是否应用缩放因子 (图像识别返回的坐标不需要缩放)
        """
        # 获取当前鼠标位置
        current_x, current_y = pyautogui.position()
        
        # 应用缩放（如果需要）
        if apply_scale:
            target_x, target_y = self.scale_coordinates(x, y)
        else:
            target_x, target_y = int(x), int(y)
        
        # 计算距离和时长
        distance = self._calculate_distance(current_x, current_y, target_x, target_y)
        duration = self._calculate_move_duration(distance)
        
        # 更新统计
        self.stats.total_distance += distance
        self.stats.total_duration += duration
        self.stats.move_count += 1
        
        if self._logger:
            speed = self.stats.avg_speed_pixels_per_second
            scale_info = "缩放" if apply_scale else "原始"
            self._logger.debug(
                f"[输入] 移动 ({scale_info}): ({current_x},{current_y}) -> ({target_x},{target_y}) | "
                f"距离={distance:.1f}px | 时长={duration:.3f}s | "
                f"平均速度={speed:.1f}px/s"
            )
        
        # 移动鼠标（贝塞尔曲线模拟人类轨迹）
        self._move_mouse_bezier(target_x, target_y, duration)
        
        # 点击
        pyautogui.click(button=button)
        
        if self._logger:
            self._logger.info(f"[输入] ✓ 点击：({x},{y}) -> ({target_x},{target_y})")
    
    def _move_mouse_bezier(self, target_x: int, target_y: int, duration: float):
        """
        使用贝塞尔曲线移动鼠标（模拟人类移动轨迹）
        
        Args:
            target_x, target_y: 目标坐标
            duration: 移动时长 (秒)
        """
        current_x, current_y = pyautogui.position()
        
        # 生成控制点（添加随机偏移模拟人类行为）
        offset_x = (target_x - current_x) * 0.3
        offset_y = (target_y - current_y) * 0.3
        control_x = (current_x + target_x) / 2 + random.uniform(-offset_x, offset_x)
        control_y = (current_y + target_y) / 2 + random.uniform(-offset_y, offset_y)
        
        # 贝塞尔曲线移动
        steps = int(duration * 100)  # 100 steps per second
        for i in range(steps + 1):
            t = i / steps
            # 二次贝塞尔曲线公式
            x = (1-t)**2 * current_x + 2*(1-t)*t * control_x + t**2 * target_x
            y = (1-t)**2 * current_y + 2*(1-t)*t * control_y + t**2 * target_y
            pyautogui.moveTo(x, y)
            time.sleep(duration / steps)
    
    def press(self, key: str, duration: int = 0):
        """
        按键
        
        Args:
            key: 按键名 (如 'space', 'enter', 'a')
            duration: 按住时长 ms (0 表示瞬间)
        """
        if duration > 0:
            pyautogui.keyDown(key)
            time.sleep(duration / 1000.0)
            pyautogui.keyUp(key)
        else:
            pyautogui.press(key)
        
        if self._logger:
            self._logger.debug(f"[输入] 按键：{key}" + (f" (按住{duration}ms)" if duration > 0 else ""))
    
    def move_mouse(self, x: int, y: int, duration: float = 0.5):
        """
        移动鼠标
        
        Args:
            x, y: 目标坐标
            duration: 移动时长 (秒)
        """
        scaled_x, scaled_y = self.scale_coordinates(x, y)
        pyautogui.moveTo(scaled_x, scaled_y, duration=duration)
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None):
        """
        滚动滚轮
        
        Args:
            clicks: 滚动量 (正数向上，负数向下)
            x, y: 可选，滚动中心坐标
        """
        if x is not None and y is not None:
            scaled_x, scaled_y = self.scale_coordinates(x, y)
            pyautogui.scroll(clicks, x=scaled_x, y=scaled_y)
        else:
            pyautogui.scroll(clicks)
    
    def delay(self, ms: int):
        """
        延迟
        
        Args:
            ms: 延迟毫秒数
        """
        time.sleep(ms / 1000.0)
    
    def get_stats(self) -> MouseStats:
        """获取鼠标移动统计"""
        return self.stats
    
    def reset_stats(self):
        """重置鼠标移动统计"""
        self.stats = MouseStats()


class InputRecorder:
    """输入录制器 - 监听输入事件"""
    
    def __init__(self, screen_manager, on_click_callback=None, on_stop_callback=None, stop_key: str = 'f12'):
        """
        Args:
            screen_manager: ScreenManager 实例
            on_click_callback: 点击回调函数 (x, y, button) -> None
            on_stop_callback: 停止回调函数 () -> None
            stop_key: 停止热键 (默认 'f12')
        """
        self.screen_manager = screen_manager
        self.on_click_callback = on_click_callback
        self.on_stop_callback = on_stop_callback
        self.stop_key = stop_key
        self.actions: List[RecordedAction] = []
        self.start_time: Optional[float] = None
        self.is_recording = False
        self._mouse_listener = None
        self._keyboard_listener = None
    
    def _get_relative_time(self) -> int:
        """获取相对时间 (ms)"""
        if self.start_time is None:
            return 0
        return int((time.time() - self.start_time) * 1000)
    
    def _on_click(self, x, y, button, pressed):
        """鼠标点击回调"""
        if not self.is_recording or not pressed:
            return
        
        # 调用截图回调（如果有）
        if self.on_click_callback:
            try:
                self.on_click_callback(x, y, button.name)
            except Exception as e:
                print(f"截图回调失败：{e}")
        
        # 获取当前活动窗口 (简化处理)
        window_title = "Unknown"
        
        action = RecordedAction(
            timestamp=self._get_relative_time(),
            action_type="mouse_click",
            x=x,
            y=y,
            button=button.name,
            window_title=window_title
        )
        self.actions.append(action)
        print(f"[录制] 鼠标点击：({x}, {y}) {button.name}")
    
    def _on_scroll(self, x, y, dx, dy):
        """鼠标滚轮回调"""
        if not self.is_recording:
            return
        
        # dy > 0 向上滚动，dy < 0 向下滚动
        if dy != 0:
            action = RecordedAction(
                timestamp=self._get_relative_time(),
                action_type="mouse_scroll",
                x=x,
                y=y,
                button="up" if dy > 0 else "down"
            )
            self.actions.append(action)
            direction = "上" if dy > 0 else "下"
            print(f"[录制] 鼠标滚轮：({x}, {y}) {direction}")
    
    def _on_move(self, x, y):
        """鼠标移动回调 (可选，通常不录制移动)"""
        pass
    
    def _on_key_press(self, key):
        """键盘按下回调"""
        if not self.is_recording:
            return
        
        try:
            key_name = key.char  # 普通字符
        except AttributeError:
            key_name = str(key).replace('Key.', '')  # 特殊键
        
        # 检测停止热键 (F12)
        if key_name.lower() == self.stop_key.lower():
            print(f"\n[录制] 检测到 {self.stop_key.upper()}，停止录制...")
            if self.on_stop_callback:
                self.on_stop_callback()
            else:
                self.stop_recording()
            return
        
        action = RecordedAction(
            timestamp=self._get_relative_time(),
            action_type="key_press",
            key=key_name
        )
        self.actions.append(action)
        print(f"[录制] 按键：{key_name}")
    
    def start_recording(self):
        """开始录制"""
        self.actions = []
        self.start_time = time.time()
        self.is_recording = True
        
        # 启动监听器
        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_move=self._on_move,
            on_scroll=self._on_scroll
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        
        self._mouse_listener.start()
        self._keyboard_listener.start()
        print(f"[录制] 已开始，按 {self.stop_key.upper()} 停止录制")
    
    def stop_recording(self) -> List[RecordedAction]:
        """停止录制并返回动作列表"""
        self.is_recording = False
        
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        
        print(f"[录制] 已停止，共录制 {len(self.actions)} 个动作")
        return self.actions
