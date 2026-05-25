"""图标状态变化监测示例

功能：持续监测指定区域内图标的状态变化，变化后返回全屏坐标
"""

import time


def main(executor):
    # 定义监测区域（百分比格式）
    region = {
        "x": (0.4, 0.6),  # 40%-60% 屏幕宽度
        "y": (0.1, 0.2)   # 10%-20% 屏幕高度
    }

    executor.log("开始监测图标状态，循环检测...", "INFO")

    # 回调函数：状态变化时调用
    def on_state_changed(new_state: str):
        executor.log(f"图标状态变化: {new_state}", "WARNING")

    while True:
        # 监测图标状态变化
        # - normal_template: 正常态图标
        # - changed_template: 变化后图标
        # - interval_ms: 检测间隔 (2秒)
        # - on_changed: 状态变化回调
        # - sound: 发出提示音 (system 表示系统提示音)
        changed, coords = executor.monitor_icon_state(
            region=region,
            normal_template="icon_before",
            changed_template="icon_after",
            interval_ms=2000,
            on_changed=on_state_changed,
            sound={"type": "system"},
            timeout=60000  # 单次检测超时 60 秒
        )

        if changed and coords:
            x, y = coords
            executor.log(f"检测到图标状态变化，位置: ({x}, {y})", "INFO")
            # 可在此处执行后续操作，如点击
            # executor.click_image(...)
            return True
        else:
            executor.log("单次检测超时，继续监测...", "DEBUG")

    return True