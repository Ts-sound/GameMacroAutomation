"""循环按键脚本（pynput）

按 config.keys 顺序循环按键，F5 开始/暂停。启动后默认暂停。

按键名：
- 鼠标：mouse_left / mouse_right / mouse_middle（在当前位置单击）
- 键盘：单字符（a、;、1）、space、enter、tab、esc、backspace、
  shift、ctrl、alt、up、down、left、right、f1..f12 等 pynput Key 名

注意：keys 中不能包含 f5（暂停热键）。
"""

import threading
import time

from pynput import keyboard, mouse

DEFAULT_KEYS = ["mouse_left", "space"]
DEFAULT_INTERVAL_MS = 300
DEFAULT_PRESS_MS = 50
POLL_S = 0.2  # 暂停时 F5 响应轮询间隔

_MOUSE_BUTTONS = {
    "mouse_left": mouse.Button.left,
    "mouse_right": mouse.Button.right,
    "mouse_middle": mouse.Button.middle,
}

_kb = keyboard.Controller()
_ms = mouse.Controller()


def _resolve(name):
    """键名 -> (是否鼠标, pynput 键/按钮)"""
    if name in _MOUSE_BUTTONS:
        return True, _MOUSE_BUTTONS[name]
    key = getattr(keyboard.Key, name, None)
    if key is not None:
        return False, key
    if len(name) == 1:
        return False, name
    raise ValueError(f"未知按键: {name}")


def _tap(is_mouse, target, press_ms):
    """单击一个键/鼠标按钮（按住 press_ms）"""
    if is_mouse:
        _ms.click(target)
        return
    _kb.press(target)
    try:
        time.sleep(press_ms / 1000.0)
    finally:
        _kb.release(target)


def _release_all():
    """释放可能残留的修饰键与鼠标按钮，异常不阻断退出"""
    for key in (keyboard.Key.shift, keyboard.Key.ctrl, keyboard.Key.alt):
        try:
            _kb.release(key)
        except Exception:
            pass
    for button in mouse.Button:
        try:
            _ms.release(button)
        except Exception:
            pass


def _sleep_while(running, seconds):
    """可被暂停打断的睡眠，最多延迟 50ms"""
    deadline = time.time() + seconds
    while running.is_set():
        remaining = deadline - time.time()
        if remaining <= 0:
            return
        time.sleep(min(0.05, remaining))


def main(executor):
    cfg = executor.get_script_config()
    names = cfg.get("keys", DEFAULT_KEYS)
    if isinstance(names, str):
        names = [names]
    names = [str(n) for n in names]
    interval_ms = int(cfg.get("interval_ms", DEFAULT_INTERVAL_MS))
    press_ms = int(cfg.get("press_ms", DEFAULT_PRESS_MS))

    if not names:
        executor.log("config.keys 为空", "ERROR")
        return False
    if any(n.lower() == "f5" for n in names):
        executor.log("config.keys 不能包含 f5（F5 为暂停热键）", "ERROR")
        return False

    try:
        resolved = [(n, *_resolve(n)) for n in names]
    except ValueError as e:
        executor.log(str(e), "ERROR")
        return False

    running = threading.Event()
    stop = threading.Event()

    def toggle():
        if running.is_set():
            running.clear()
            _release_all()
            executor.log("已暂停，按 F5 继续", "WARNING")
        else:
            running.set()
            executor.log("开始循环按键，按 F5 暂停", "INFO")

    def on_press(key):
        if key == keyboard.Key.f5:
            toggle()

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    executor.log(f"按键列表 {names} | 间隔 {interval_ms}ms | 按住 {press_ms}ms", "INFO")
    executor.log("按 F5 开始/暂停，Ctrl+C 退出", "INFO")

    try:
        while not stop.is_set():
            if not running.wait(POLL_S):
                continue
            for name, is_mouse, target in resolved:
                if not running.is_set():
                    break
                _tap(is_mouse, target, press_ms)
                _sleep_while(running, interval_ms / 1000.0)
    except KeyboardInterrupt:
        executor.log("收到 Ctrl+C，退出", "INFO")
    finally:
        running.clear()
        listener.stop()
        _release_all()

    return True
