"""RF4 钓鱼自动脚本 - 状态机实现

状态:
- WAIT_READY:     等待抛竿，检测 01_ready        -> 单击 ;        进入 WAIT_BITE
- WAIT_BITE:      等待中鱼，检测 02_on_fish       -> 长按 ;        进入 REELING_FISH
                  检测 04_move_in_bottom          -> 长按 ;        进入 REELING_BOTTOM
- REELING_FISH:   中鱼收线中，检测 03_keep        -> 停+单击 空格  回到 WAIT_READY
                  检测 04_move_in_bottom          -> 停（鱼挣脱）  回到 WAIT_READY
                  按满超时                        -> 停            回到 WAIT_READY
- REELING_BOTTOM: 沉底收线中，检测 02_on_fish     -> 停+续长按 ;   进入 REELING_FISH
                  检测 01_ready                   -> 停（收完）    回到 WAIT_READY
                  按满超时                        -> 续长按（继续收）

检测设置（yaml detection_zones）:
- center: 区域中心位置（绝对像素，可配置）
- size: 区域尺寸（可配置）
- grayscale: 灰度匹配
- confidence: 置信度

检测频率 detect_interval_ms（默认 500ms）:
- 主循环轮询与长按中断检查共用同一频率

快捷键控制:
- ctrl+alt+o  启动自动化（从 WAIT_READY 开始）
- ctrl+alt+p  停止（暂停回空闲，可再启动；长按收线中立即释放）
"""

import threading
import time

from esp32_keyboard import DEFAULT_HOST, DEFAULT_PORT, Esp32Keyboard
from pynput import keyboard

DEFAULT_TAP_MS = 50
DEFAULT_HOLD_MS = 400
DEFAULT_INTERVAL_MS = 500

# 状态定义
STATE_READY = "WAIT_READY"  # 等待抛竿
STATE_BITE = "WAIT_BITE"  # 等待中鱼
STATE_REEL_FISH = "REELING_FISH"  # 中鱼收线中
STATE_REEL_BOTTOM = "REELING_BOTTOM"  # 沉底收线中
STATE_STOP = "STOPPED"  # 停止
STATE_INIT = STATE_READY

# 长按中断哨兵：停止热键触发
STOP_SIGNAL = "__STOP__"


def _detect_zone(executor, zones, name):
    """检测指定区域，返回是否命中"""
    zone = zones.get(name)
    if not zone:
        return False
    return executor.detect_in_center_region(
        zone["center"],
        zone["size"],
        name,
        zone.get("confidence", 0.8),
        zone.get("grayscale", True),
    )


def _interrupt_check(executor, zones, stop_event, *names):
    """返回中断条件：返回首个命中的区域名或 STOP_SIGNAL，全部未命中返回 None"""

    def check():
        if stop_event.is_set():
            return STOP_SIGNAL
        for n in names:
            if _detect_zone(executor, zones, n):
                return n
        return None

    return check


def _hold(executor, kb, zones, key, hold_ms, interval_ms, stop_event, *watch_names):
    """可中断长按，返回触发区域名/STOP_SIGNAL（按满返回 None）"""
    return kb.hold_interruptible(
        key,
        duration_ms=hold_ms,
        interrupt_check=_interrupt_check(executor, zones, stop_event, *watch_names),
        interval_ms=interval_ms,
    )


def step(executor, kb, state, zones, tap_ms, hold_ms, interval_ms, stop_event):
    """状态机单步执行，返回下一个状态"""
    if state == STATE_READY:
        if _detect_zone(executor, zones, "01_ready"):
            executor.log(f"[{state}] 检测到 01_ready -> tap ;", "INFO")
            kb.tap(";", press_ms=tap_ms)
            return STATE_BITE
        return STATE_READY

    if state == STATE_BITE:
        if _detect_zone(executor, zones, "02_on_fish"):
            executor.log(f"[{state}] 检测到 02_on_fish -> hold ;", "INFO")
            return STATE_REEL_FISH
        if _detect_zone(executor, zones, "04_move_in_bottom"):
            executor.log(f"[{state}] 检测到 04_move_in_bottom -> hold ;", "INFO")
            return STATE_REEL_BOTTOM
        return STATE_BITE

    if state == STATE_REEL_FISH:
        fired = _hold(
            executor, kb, zones, ";", hold_ms, interval_ms, stop_event,
            "03_keep", "04_move_in_bottom",
        )
        if fired == STOP_SIGNAL:
            executor.log("[REELING_FISH] 停止热键 -> 停", "INFO")
            return STATE_STOP
        if fired == "03_keep":
            executor.log("[REELING_FISH] 03_keep 出现 -> 停 + tap 空格", "INFO")
            kb.tap("space", press_ms=tap_ms)
            return STATE_READY
        if fired == "04_move_in_bottom":
            executor.log("[REELING_FISH] 04 出现（鱼挣脱）-> 停", "INFO")
            return STATE_READY
        executor.log("[REELING_FISH] 按满超时 -> 停", "INFO")
        return STATE_READY

    if state == STATE_REEL_BOTTOM:
        fired = _hold(
            executor, kb, zones, ";", hold_ms, interval_ms, stop_event,
            "01_ready", "02_on_fish",
        )
        if fired == STOP_SIGNAL:
            executor.log("[REELING_BOTTOM] 停止热键 -> 停", "INFO")
            return STATE_STOP
        if fired == "02_on_fish":
            executor.log("[REELING_BOTTOM] 02_on_fish 出现 -> 续 hold ;", "INFO")
            return STATE_REEL_FISH
        if fired == "01_ready":
            executor.log("[REELING_BOTTOM] 01_ready 出现（收完）-> 停", "INFO")
            return STATE_READY
        executor.log("[REELING_BOTTOM] 按满超时 -> 继续收线", "INFO")
        return STATE_REEL_BOTTOM

    return state


def _run_loop(executor, kb, zones, tap_ms, hold_ms, interval_ms, stop_event):
    """运行自动化主循环，停止热键触发时退出"""
    state = STATE_INIT
    executor.log(f"启动自动化，初始状态: {state}", "INFO")
    while not stop_event.is_set():
        state = step(
            executor, kb, state, zones, tap_ms, hold_ms, interval_ms, stop_event
        )
        if state == STATE_STOP:
            break
        time.sleep(interval_ms / 1000.0)
    executor.log("自动化已停止", "INFO")


def main(executor):
    cfg = executor.get_script_config()
    zones = executor.get_detection_zones()

    host = cfg.get("esp32_host", DEFAULT_HOST)
    port = int(cfg.get("esp32_port", DEFAULT_PORT))
    tap_ms = int(cfg.get("tap_ms", DEFAULT_TAP_MS))
    hold_ms = int(cfg.get("hold_ms", DEFAULT_HOLD_MS))
    interval_ms = int(cfg.get("detect_interval_ms", DEFAULT_INTERVAL_MS))

    start_event = threading.Event()
    stop_event = threading.Event()
    hotkeys = keyboard.GlobalHotKeys(
        {
            "<ctrl>+<alt>+o": start_event.set,
            "<ctrl>+<alt>+p": stop_event.set,
        }
    )

    kb = Esp32Keyboard(host=host, port=port)
    try:
        kb.connect()
        executor.log(f"ESP32 已连接 {host}:{port}", "INFO")
        executor.log(
            f"长按时长 {hold_ms}ms，单击时长 {tap_ms}ms，检测频率 {interval_ms}ms",
            "INFO",
        )
        hotkeys.start()
        executor.log("快捷键: ctrl+alt+o 启动 / ctrl+alt+p 停止", "INFO")

        while True:
            start_event.wait()
            start_event.clear()
            stop_event.clear()
            _run_loop(executor, kb, zones, tap_ms, hold_ms, interval_ms, stop_event)
            kb.release_all()
    finally:
        hotkeys.stop()
        # 兜底：确保无按键残留按住
        kb.release_all()
        kb.close()

    return True
