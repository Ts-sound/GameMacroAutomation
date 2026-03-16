"""输入控制模块 - 封装 pyautogui 和 pynput"""
import time
from dataclasses import dataclass
from typing import Optional, List
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


class InputController:
    """输入控制器 - 执行动作"""
    
    def __init__(self, scale_factor: float = 1.0):
        """
        Args:
            scale_factor: 坐标缩放因子
        """
        self.scale_factor = scale_factor
        # 配置 pyautogui
        pyautogui.FAILSAFE = True  # 鼠标移到屏幕角落触发故障保护
        pyautogui.PAUSE = 0.1  # 操作间默认延迟
    
    def scale_coordinates(self, x: int, y: int) -> tuple[int, int]:
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


class InputRecorder:
    """输入录制器 - 监听输入事件"""
    
    def __init__(self, screen_manager, on_click_callback=None):
        """
        Args:
            screen_manager: ScreenManager 实例
            on_click_callback: 点击回调函数 (x, y, button) -> None
        """
        self.screen_manager = screen_manager
        self.on_click_callback = on_click_callback
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
            on_move=self._on_move
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press
        )
        
        self._mouse_listener.start()
        self._keyboard_listener.start()
        print("[录制] 已开始，按 Ctrl+C 停止")
    
    def stop_recording(self) -> List[RecordedAction]:
        """停止录制并返回动作列表"""
        self.is_recording = False
        
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        
        print(f"[录制] 已停止，共录制 {len(self.actions)} 个动作")
        return self.actions
