"""图标状态变化监测示例

功能：持续监测指定区域内图标的状态变化，变化后返回全屏坐标

支持两种检测模式：
- template 模式：使用 pyautogui 模板匹配（默认，向后兼容）
- histogram 模式：使用颜色直方图对比，解决同形异色问题
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

    # ========== 示例 1: template 模式（默认，向后兼容）==========
    # 使用 pyautogui 模板匹配，适用于形状差异明显的图标
    changed, coords = executor.monitor_icon_state(
        region=region,
        normal_template="icon_before",
        changed_template="icon_after",           # 单个模板
        # changed_template=["icon_after", "icon_after2"],  # 或多个模板
        color_mode="template",                   # 默认值，可省略
        interval_ms=500,
        on_changed=on_state_changed,
        sound={"type": "system"},
        timeout=60000
    )

    if changed and coords:
        x, y = coords
        executor.log(f"[template模式] 检测到图标状态变化，位置: ({x}, {y})", "INFO")
        return True

    # ========== 示例 2: histogram 模式 ==========
    # 使用颜色直方图对比，适用于形状相同但颜色不同的图标
    changed, coords = executor.monitor_icon_state(
        region=region,
        normal_template="icon_before",
        changed_template=["icon_after", "icon_after2"],  # 支持多个变化态模板
        color_mode="histogram",           # 使用直方图对比
        histogram_threshold=0.7,          # 相似度阈值，越高越严格
        interval_ms=500,
        on_changed=on_state_changed,
        sound={"type": "system"},
        timeout=60000
    )

    if changed and coords:
        x, y = coords
        executor.log(f"[histogram模式] 检测到图标状态变化，位置: ({x}, {y})", "INFO")
        # 可在此处执行后续操作，如点击
        # executor.click_image(...)
        return True

    executor.log("监测超时或未检测到变化", "WARNING")
    return False