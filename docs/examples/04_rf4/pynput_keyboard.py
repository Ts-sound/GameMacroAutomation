"""pynput 键盘后端

与 esp32_keyboard.Esp32Keyboard 相同的按键 API，rf4_lure 通过
config.keyboard_backend 在 esp32 / pynput 之间切换。

按键名：
- 鼠标：mouse_left / mouse_right / mouse_middle
- 键盘：单字符（;、'、1）、space、enter、shift、ctrl、alt、f1 等 pynput Key 名
"""

import threading
import time

from pynput import keyboard, mouse

DEFAULT_PRESS_MS = 50

_MOUSE_BUTTONS = {
    "mouse_left": mouse.Button.left,
    "mouse_right": mouse.Button.right,
    "mouse_middle": mouse.Button.middle,
}


class PynputKeyboard:
    """pynput 键盘客户端（API 兼容 Esp32Keyboard）"""

    def __init__(self):
        self._kb = keyboard.Controller()
        self._ms = mouse.Controller()
        self._held = set()  # {(is_mouse, target)}
        self._lock = threading.Lock()

    # ========== 连接管理 ==========

    def connect(self):
        """无网络连接，保持 API 兼容"""

    def close(self):
        """释放按键（无连接可关）"""
        self.release_all()

    # ========== 键名解析 ==========

    def _resolve(self, name: str):
        """键名 -> (是否鼠标, pynput 键/按钮)"""
        if name in _MOUSE_BUTTONS:
            return True, _MOUSE_BUTTONS[name]
        if len(name) == 1:
            return False, name
        key = getattr(keyboard.Key, name, None)
        if key is None:
            raise ValueError(f"未知按键: {name}")
        return False, key

    # ========== 键盘操作 ==========

    def tap(self, key: str, press_ms: int = DEFAULT_PRESS_MS):
        """单击（短按）"""
        self.press(key)
        try:
            time.sleep(press_ms / 1000.0)
        finally:
            self.release(key)

    def hold(self, key: str, duration_ms: int):
        """长按"""
        self.press(key)
        try:
            time.sleep(duration_ms / 1000.0)
        finally:
            self.release(key)

    def hold_interruptible(self, key, duration_ms, interrupt_check=None, interval_ms=50):
        """可中断长按，返回中断触发值；按满返回 None"""
        self.press(key)
        fired = None
        deadline = time.time() + duration_ms / 1000.0
        try:
            while True:
                if interrupt_check is not None:
                    fired = interrupt_check()
                    if fired:
                        break
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                time.sleep(min(interval_ms / 1000.0, remaining))
        finally:
            self.release(key)
        return fired

    def combo_hold_interruptible(
        self, keys, duration_ms, interrupt_check=None, interval_ms=50
    ):
        """可中断组合键长按，中断/结束释放全部按键"""
        for key in keys:
            self.press(key)
        fired = None
        deadline = time.time() + duration_ms / 1000.0
        try:
            while True:
                if interrupt_check is not None:
                    fired = interrupt_check()
                    if fired:
                        break
                remaining = deadline - time.time()
                if remaining <= 0:
                    break
                time.sleep(min(interval_ms / 1000.0, remaining))
        finally:
            for key in reversed(keys):
                self.release(key)
        return fired

    def combo(self, keys, press_ms: int = DEFAULT_PRESS_MS):
        """组合键，如 ['shift', ';']"""
        for key in keys:
            self.press(key)
        time.sleep(press_ms / 1000.0)
        for key in reversed(keys):
            self.release(key)

    def press(self, key: str):
        """按下按键（不自动释放）"""
        is_mouse, target = self._resolve(key)
        with self._lock:
            if is_mouse:
                self._ms.press(target)
            else:
                self._kb.press(target)
            self._held.add((is_mouse, target))

    def release(self, key: str):
        """释放按键"""
        is_mouse, target = self._resolve(key)
        with self._lock:
            self._release_target(is_mouse, target)

    def release_all(self):
        """释放所有已按下按键"""
        with self._lock:
            for is_mouse, target in list(self._held):
                self._release_target(is_mouse, target)
            self._held.clear()

    def _release_target(self, is_mouse, target):
        try:
            if is_mouse:
                self._ms.release(target)
            else:
                self._kb.release(target)
        except Exception:
            pass
        self._held.discard((is_mouse, target))

    # ========== 上下文管理器 ==========

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
