"""RF4 钓鱼自动脚本 - 路亚直收（lure）状态机实现

流程:
1. WAIT_READY:  命中 01_ready            -> combo shift+; 抛出   进入 WAIT_SINK
2. WAIT_SINK:   等待 cast_wait_ms(默认4s)  -> 开始打状态           进入 JIGGING
                期间命中 02_on_fish       -> 开始加速收线         进入 REELING_FISH
3. JIGGING:     打状态 ';' 按 jig_press_ms(默认1s) / 松 jig_release_ms(默认3s) 循环
                命中 02_on_fish           -> 停打状态             进入 REELING_FISH
4. REELING_FISH: 长按 shift+;+' 加速收线
                命中 03_keep              -> 停 + tap space 入户   回到 WAIT_READY
                命中 01_ready             -> 停（收完）           回到 WAIT_READY
                按满超时                  -> 续长按（继续收）
5. STOP:        停止

检测设置（yaml detection_zones）:
- center: 区域中心位置（绝对像素，可配置）
- size: 区域尺寸（可配置）
- grayscale: 灰度匹配
- confidence: 置信度

检测频率 detect_interval_ms（默认 500ms）:
- 主循环轮询与长按中断检查共用同一频率

快捷键控制:
- ctrl+alt+o  启动自动化（从 WAIT_READY 开始）
- ctrl+alt+p  停止（暂停回空闲，可再启动；收线/打状态中立即释放按键）
- ctrl+c      优雅退出整个脚本

日志格式（状态变化时打印）:
- [当前状态] | 事件 | 动作 | 目标状态
- 检测命中同时打印位置与置信度
"""

import threading
import time

from esp32_keyboard import DEFAULT_HOST, DEFAULT_PORT, Esp32Keyboard
from pynput import keyboard

DEFAULT_TAP_MS = 100
DEFAULT_HOLD_MS = 300000
DEFAULT_INTERVAL_MS = 500
DEFAULT_CAST_WAIT_MS = 4000
DEFAULT_JIG_PRESS_MS = 1000
DEFAULT_JIG_RELEASE_MS = 3000

# 状态定义
STATE_READY = "WAIT_READY"  # 等待抛竿
STATE_SINK = "WAIT_SINK"  # 抛出后等待下沉
STATE_JIG = "JIGGING"  # 打状态
STATE_REEL_FISH = "REELING_FISH"  # 中鱼加速收线中
STATE_STOP = "STOPPED"  # 停止
STATE_INIT = STATE_READY

# 长按中断哨兵：停止热键触发
STOP_SIGNAL = "__STOP__"


def _locate_zone(executor, zones, name):
    """检测指定区域，命中返回 {"x", "y", "score"}，未命中返回 None

    使用区域配置的 image 路径作为模板（不再依赖区域名与图片名一致）。
    """
    zone = zones.get(name)
    if not zone:
        return None
    return executor.locate_zone_details(
        zone["center"],
        zone["size"],
        zone["image"],
        zone.get("confidence", 0.8),
        zone.get("grayscale", True),
    )


def _describe(details):
    """格式化位置+置信度"""
    if not details:
        return ""
    score = details.get("score")
    if score is None:
        return f"({details['x']}, {details['y']})"
    return f"({details['x']}, {details['y']}) conf={score:.3f}"


def _transition(executor, state, event, action, next_state, details=None):
    """状态变化日志：[当前状态] | 事件 | 动作 | 目标状态"""
    desc = f" {_describe(details)}" if details else ""
    executor.log(f"[{state}] | {event}{desc} -> {action} -> {next_state}", "INFO")


def _interrupt_check(executor, zones, stop_event, *names):
    """返回中断条件：返回首个命中的区域名或 STOP_SIGNAL，全部未命中返回 None"""

    def check():
        if stop_event.is_set():
            return STOP_SIGNAL
        for n in names:
            if _locate_zone(executor, zones, n):
                return n
        return None

    return check


def _combo_hold(
    executor, kb, zones, keys, hold_ms, interval_ms, stop_event, *watch_names
):
    """可中断组合键长按，返回触发区域名/STOP_SIGNAL（按满返回 None）"""
    return kb.combo_hold_interruptible(
        keys,
        duration_ms=hold_ms,
        interrupt_check=_interrupt_check(executor, zones, stop_event, *watch_names),
        interval_ms=interval_ms,
    )


def _wait_sink(executor, zones, cast_wait_ms, interval_ms, stop_event):
    """抛出后等待下沉，期间命中 02_on_fish 提前收线

    Returns:
        目标状态：JIGGING（等满）或 REELING_FISH（提前上鱼）或 STOP
    """
    deadline = time.time() + cast_wait_ms / 1000.0
    while not stop_event.is_set():
        pos = _locate_zone(executor, zones, "02_on_fish")
        if pos:
            _transition(
                executor, STATE_SINK, "02_on_fish", "开始加速收线", STATE_REEL_FISH, pos
            )
            return STATE_REEL_FISH
        remaining = deadline - time.time()
        if remaining <= 0:
            _transition(
                executor,
                STATE_SINK,
                f"等满{cast_wait_ms}ms",
                "开始打状态",
                STATE_JIG,
            )
            return STATE_JIG
        time.sleep(min(interval_ms / 1000.0, remaining))
    return STATE_STOP


def _jigging(
    executor, kb, zones, interval_ms, stop_event, jig_press_ms, jig_release_ms
):
    """打状态：; 按 jig_press_ms / 松 jig_release_ms 循环，等待上鱼

    Returns:
        目标状态：REELING_FISH（上鱼）或 STOP
    """
    while not stop_event.is_set():
        fired = kb.hold_interruptible(
            ";",
            duration_ms=jig_press_ms,
            interrupt_check=_interrupt_check(executor, zones, stop_event, "02_on_fish"),
            interval_ms=interval_ms,
        )
        if fired == STOP_SIGNAL:
            return STATE_STOP
        if fired == "02_on_fish":
            _transition(executor, STATE_JIG, "02_on_fish", "停打状态", STATE_REEL_FISH)
            return STATE_REEL_FISH
        if stop_event.is_set():
            return STATE_STOP
        # 松开停 jig_release_ms，期间也检测上鱼
        deadline = time.time() + jig_release_ms / 1000.0
        while not stop_event.is_set():
            if _locate_zone(executor, zones, "02_on_fish"):
                _transition(
                    executor, STATE_JIG, "02_on_fish", "停打状态", STATE_REEL_FISH
                )
                return STATE_REEL_FISH
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            time.sleep(min(interval_ms / 1000.0, remaining))
    return STATE_STOP


def step(
    executor,
    kb,
    state,
    zones,
    tap_ms,
    hold_ms,
    interval_ms,
    stop_event,
    cast_wait_ms,
    jig_press_ms,
    jig_release_ms,
):
    """状态机单步执行，返回下一个状态"""
    if state == STATE_READY:
        pos = _locate_zone(executor, zones, "01_ready")
        if pos:
            _transition(
                executor, state, "01_ready", "combo shift+; 抛出", STATE_SINK, pos
            )
            kb.combo(["shift", ";"], press_ms=tap_ms)
            return STATE_SINK
        return STATE_READY

    if state == STATE_SINK:
        return _wait_sink(executor, zones, cast_wait_ms, interval_ms, stop_event)

    if state == STATE_JIG:
        return _jigging(
            executor, kb, zones, interval_ms, stop_event, jig_press_ms, jig_release_ms
        )

    if state == STATE_REEL_FISH:
        fired = _combo_hold(
            executor,
            kb,
            zones,
            ["shift", ";", "'"],
            hold_ms,
            interval_ms,
            stop_event,
            "03_keep",
            "01_ready",
        )
        if fired == STOP_SIGNAL:
            _transition(executor, state, "停止热键", "停", STATE_STOP)
            return STATE_STOP
        if fired:
            pos = _locate_zone(executor, zones, fired)
            if fired == "03_keep":
                _transition(
                    executor, state, "03_keep", "停+单击 空格", STATE_READY, pos
                )
                time.sleep(0.5)
                kb.tap("space", press_ms=tap_ms)
                return STATE_READY
            _transition(executor, state, "01_ready", "停", STATE_READY, pos)
            return STATE_READY
        executor.log(f"[{state}] | 按满超时 -> 继续收线", "INFO")
        return STATE_REEL_FISH

    return state


def _run_loop(
    executor,
    kb,
    zones,
    tap_ms,
    hold_ms,
    interval_ms,
    stop_event,
    cast_wait_ms,
    jig_press_ms,
    jig_release_ms,
):
    """运行自动化主循环，停止热键触发时退出"""
    state = STATE_INIT
    executor.log(f"启动自动化，初始状态: [{state}]", "INFO")
    while not stop_event.is_set():
        state = step(
            executor,
            kb,
            state,
            zones,
            tap_ms,
            hold_ms,
            interval_ms,
            stop_event,
            cast_wait_ms,
            jig_press_ms,
            jig_release_ms,
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
    cast_wait_ms = int(cfg.get("cast_wait_ms", DEFAULT_CAST_WAIT_MS))
    jig_press_ms = int(cfg.get("jig_press_ms", DEFAULT_JIG_PRESS_MS))
    jig_release_ms = int(cfg.get("jig_release_ms", DEFAULT_JIG_RELEASE_MS))

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
        executor.log(
            f"抛竿等待 {cast_wait_ms}ms | "
            f"打状态: ; 按 {jig_press_ms}ms / 松 {jig_release_ms}ms",
            "INFO",
        )
        hotkeys.start()
        executor.log(
            "快捷键: ctrl+alt+o 启动 / ctrl+alt+p 停止 / ctrl+c 退出",
            "INFO",
        )

        while True:
            start_event.wait()
            start_event.clear()
            stop_event.clear()
            _run_loop(
                executor,
                kb,
                zones,
                tap_ms,
                hold_ms,
                interval_ms,
                stop_event,
                cast_wait_ms,
                jig_press_ms,
                jig_release_ms,
            )
            kb.release_all()
    except KeyboardInterrupt:
        executor.log("收到 ctrl+c，优雅退出...", "INFO")
    except Exception as e:
        import traceback

        executor.log(f"运行异常: {e}", "ERROR")
        executor.log(f"堆栈: {traceback.format_exc()}", "INFO")
    finally:
        _safe_stop(hotkeys)
        _safe_release(kb)
        executor.log("已退出", "INFO")

    return True


def _safe_stop(hotkeys):
    """安全停止热键监听，异常不阻断清理"""
    try:
        hotkeys.stop()
    except Exception:
        pass


def _safe_release(kb):
    """安全释放按键并关闭连接，异常不阻断清理"""
    try:
        kb.release_all()
    except Exception:
        pass
    try:
        kb.close()
    except Exception:
        pass
