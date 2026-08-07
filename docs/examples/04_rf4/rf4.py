"""RF4 钓鱼自动脚本 - 状态机实现

状态:
- WAIT_CAST: 等待抛竿，检测 01_ready -> 单击 ;   进入 WAIT_FISH
- WAIT_FISH: 等待中鱼，检测 02_on_fish -> 长按 ; 进入 WAIT_KEEP
- WAIT_KEEP: 等待收鱼，检测 03_keep   -> 单击 空格 回到 WAIT_CAST

通用收线（沉底）: 任意状态检测 04_move_in_bottom -> 长按 ; 回到 WAIT_CAST

检测设置（yaml detection_zones）:
- center: 区域中心位置（绝对像素，可配置）
- size: 区域尺寸（可配置）
- grayscale: 灰度匹配
- confidence: 置信度
"""

from esp32_keyboard import DEFAULT_HOST, DEFAULT_PORT, Esp32Keyboard

DEFAULT_TAP_MS = 50
DEFAULT_HOLD_MS = 400

# 状态定义
STATE_CAST = "WAIT_CAST"  # 等待抛竿
STATE_FISH = "WAIT_FISH"  # 等待中鱼
STATE_KEEP = "WAIT_KEEP"  # 等待收鱼
STATE_INIT = STATE_CAST

# 主状态转换: 状态 -> [(区域名, 动作, 按键, 目标状态)]
TRANSITIONS = {
    STATE_CAST: [("01_ready", "tap", ";", STATE_FISH)],
    STATE_FISH: [("02_on_fish", "hold", ";", STATE_KEEP)],
    STATE_KEEP: [("03_keep", "tap", "space", STATE_CAST)],
}

# 通用沉底收线: (区域名, 动作, 按键)
BOTTOM_RECOVER = ("04_move_in_bottom", "hold", ";")


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


def _do_action(executor, kb, zones, action, key, tap_ms, hold_ms, interrupt_check=None):
    """执行按键动作

    hold 使用可中断长按：按住期间周期检查 interrupt_check()，
    返回非空值（如区域名）立即释放。

    Returns:
        tap: False；hold: 中断触发值（区域名），按满时长返回 None
    """
    if action == "tap":
        kb.tap(key, press_ms=tap_ms)
        return False
    return kb.hold_interruptible(
        key, duration_ms=hold_ms, interrupt_check=interrupt_check
    )


def _interrupt_check(executor, zones, *names):
    """返回中断条件：返回首个命中的区域名，全部未命中返回 None"""

    def check():
        for n in names:
            if _detect_zone(executor, zones, n):
                return n
        return None

    return check


def step(executor, kb, state, zones, tap_ms, hold_ms):
    """状态机单步执行，返回下一个状态

    优先级:
    1. 沉底收线（04_move_in_bottom）任意状态生效
    2. 当前状态的主转换
    3. 未命中保持当前状态

    长按期间图标变化:
    - 长按收线时，若 02_on_fish（中鱼）出现立即松开 -> WAIT_FISH
    - 长按收线时，若 03_keep（可收）出现立即松开 -> WAIT_KEEP
    """
    # 1. 通用沉底收线
    name, action, key = BOTTOM_RECOVER
    if _detect_zone(executor, zones, name):
        executor.log(f"[{state}] 检测到 {name} -> 长按 {key}", "INFO")
        fired = _do_action(
            executor, kb, zones, action, key, tap_ms, hold_ms,
            interrupt_check=_interrupt_check(executor, zones, "02_on_fish", "03_keep"),
        )
        if fired == "02_on_fish":
            return STATE_FISH
        if fired == "03_keep":
            return STATE_KEEP
        return STATE_CAST

    # 2. 主转换
    for zone_name, action, key, next_state in TRANSITIONS[state]:
        if _detect_zone(executor, zones, zone_name):
            executor.log(f"[{state}] 检测到 {zone_name} -> {action} {key}", "INFO")
            fired = _do_action(
                executor, kb, zones, action, key, tap_ms, hold_ms,
                interrupt_check=_interrupt_check(executor, zones, "03_keep"),
            )
            if fired == "03_keep":
                return STATE_KEEP
            return next_state

    # 3. 未命中
    return state


def main(executor):
    cfg = executor.get_script_config()
    zones = executor.get_detection_zones()

    host = cfg.get("esp32_host", DEFAULT_HOST)
    port = int(cfg.get("esp32_port", DEFAULT_PORT))
    tap_ms = int(cfg.get("tap_ms", DEFAULT_TAP_MS))
    hold_ms = int(cfg.get("hold_ms", DEFAULT_HOLD_MS))

    kb = Esp32Keyboard(host=host, port=port)
    try:
        kb.connect()
        executor.log(f"ESP32 已连接 {host}:{port}", "INFO")
        executor.log(f"长按时长 {hold_ms}ms，单击时长 {tap_ms}ms", "INFO")

        state = STATE_INIT
        executor.log(f"初始状态: {state}", "INFO")
        while True:
            state = step(executor, kb, state, zones, tap_ms, hold_ms)
    finally:
        # 兜底：确保无按键残留按住
        kb.release_all()
        kb.close()

    return True
