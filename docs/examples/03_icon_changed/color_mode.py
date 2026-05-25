"""图标状态变化监测示例 - color 模式（推荐）

功能：使用去背景模板 + alpha 通道提取颜色，对比初始颜色变化

适用于：形状相同但颜色不同的图标（如进度条颜色变化）
无需提供 icon_after 模板
"""

def main(executor):
    region = {
        "x": (0.0, 1.0),  # 全屏检测
        "y": (0.0, 1.0)
    }

    executor.log("开始监测图标状态（color模式）...", "INFO")

    def on_state_changed(new_state: str):
        executor.log(f"图标状态变化: {new_state}", "WARNING")

    while True:
        changed, coords = executor.monitor_icon_state(
            region=region,
            normal_template="icon_before_nobg",    # 去背景模板
            changed_template=[],                    # color 模式不需要
            color_mode="color",                     # 颜色对比模式
            color_diff_threshold=0.15,              # 颜色差异阈值
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