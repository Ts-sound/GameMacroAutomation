"""图标状态变化监测示例 - histogram 模式

功能：使用颜色直方图对比监测图标状态变化

适用于：形状相同但颜色不同的图标（如进度条颜色变化）
"""

def main(executor):
    region = {
      "x": (0.0, 1.0),
      "y": (0.0, 1.0)
    }

    executor.log("开始监测图标状态（histogram模式）...", "INFO")

    def on_state_changed(new_state: str):
        executor.log(f"图标状态变化: {new_state}", "WARNING")

    while True:
        changed, coords = executor.monitor_icon_state(
            region=region,
            normal_template="icon_before",
            changed_template=["icon_after", "icon_after2"],  # 支持多个变化态模板
            color_mode="histogram",
            histogram_threshold=0.7,   # 相似度阈值，越高越严格
            interval_ms=500,
            on_changed=on_state_changed,
            sound={"type": "system"},
            timeout=60000
        )

        if changed and coords:
            x, y = coords
            executor.log(f"检测到图标状态变化，位置: ({x}, {y})", "INFO")
            return True
        else:
            executor.log("单次检测超时，继续监测...", "DEBUG")

    return True