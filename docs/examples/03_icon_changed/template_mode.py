"""图标状态变化监测示例 - template 模式

功能：使用 pyautogui 模板匹配监测图标状态变化

适用于：形状差异明显的图标（如形状完全不同）
"""


def main(executor):
    region = {"x": (0.0, 1.0), "y": (0.0, 1.0)}

    executor.log("开始监测图标状态（template模式）...", "INFO")

    def on_state_changed(new_state: str):
        executor.log(f"图标状态变化: {new_state}", "WARNING")

    while True:
        changed, coords = executor.monitor_icon_state(
            region=region,
            normal_template="icon_before",
            changed_template=["icon_after", "icon_after2"],  # 或多个模板
            color_mode="template",  # 默认值，可省略
            interval_ms=500,
            on_changed=on_state_changed,
            sound={"type": "system"},
            timeout=60000,
        )

        if changed and coords:
            x, y = coords
            executor.log(f"检测到图标状态变化，位置: ({x}, {y})", "INFO")
        else:
            executor.log("单次检测超时，继续监测...", "DEBUG")

    return True
