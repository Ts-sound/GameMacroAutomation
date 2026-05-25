"""图标状态变化监测示例

功能：监测指定区域内图标的状态变化，变化后发出提示音
"""


def main(executor):
    # 定义监测区域（百分比格式）
    region = {
        "x": (0.4, 0.6),  # 40%-60% 屏幕宽度
        "y": (0.1, 0.2)   # 10%-20% 屏幕高度
    }

    # 回调函数：状态变化时调用
    def on_state_changed(new_state: str):
        executor.log(f"图标状态变化: {new_state}", "WARNING")

    # 监测图标状态变化
    # - normal_template: 正常态图标
    # - changed_template: 变化后图标
    # - interval_ms: 检测间隔 (2秒)
    # - on_changed: 状态变化回调
    # - sound: 发出提示音 (system 表示系统提示音)
    result = executor.monitor_icon_state(
        region=region,
        normal_template="icon_before",
        changed_template="icon_after",
        interval_ms=2000,
        on_changed=on_state_changed,
        sound={"type": "system"},
        timeout=60000  # 最多监测 60 秒
    )

    if result:
        executor.log("检测到图标状态变化", "INFO")
    else:
        executor.log("监测超时，未检测到变化", "WARNING")

    return True