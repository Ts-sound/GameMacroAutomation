"""
战斗循环示例 - Python 脚本

使用 Python 控制条件循环执行战斗流程
"""


def main(executor):
    """
    主函数 - 脚本入口
    
    Args:
        executor: ScriptAPI 实例，提供所有可用的 API
    """
    executor.log("=== 战斗循环开始 ===", "INFO")
    
    # 等待战斗开始（Boss 血条出现）
    executor.log("等待 Boss 出现...", "INFO")
    if not executor.wait_image("boss_hp_bar", 10000):
        executor.log("Boss 未出现，退出", "ERROR")
        return False
    
    # 循环 1: 使用 loop_while - 当 Boss 血条存在时继续攻击
    attack_count = 0
    max_iterations = 100
    
    executor.log("开始战斗循环...", "INFO")
    executor.loop_while(
        lambda: executor.image_exists("boss_hp_bar", 0.7),
        lambda: _attack_body(executor, attack_count),
        max_iterations,
        1000
    )
    
    executor.log("战斗结束，攻击次数：" + str(attack_count), "INFO")
    
    # 循环 2: 使用 loop_times - 固定次数拾取物品
    executor.log("拾取物品...", "INFO")
    executor.loop_times(
        5,  # 拾取 5 次
        lambda: (
            executor.click_image("item_1", 0.8),
            executor.delay(500)
        ),
        200  # 每次间隔 200ms
    )
    
    # 循环 3: 使用 loop_until - 直到奖励弹窗出现
    executor.log("等待奖励弹窗...", "INFO")
    executor.loop_until(
        lambda: executor.image_exists("reward_popup", 0.8),
        lambda: (
            executor.click_image("collect_btn", 0.8),
            executor.delay(1000)
        ),
        30000,  # 超时 30 秒
        2000    # 每 2 秒检查一次
    )
    
    # 领取奖励
    if executor.image_exists("reward_popup", 0.8):
        executor.log("领取奖励", "INFO")
        executor.click_image("reward_popup", 0.9)
        executor.delay(500)
    
    executor.log("=== 战斗循环结束 ===", "INFO")
    return True


def _attack_body(executor, attack_count):
    """攻击循环体"""
    attack_count += 1
    executor.log(f"第 {attack_count} 次攻击", "INFO")
    
    # 检查是否需要喝药水
    if executor.image_exists("low_hp_warning", 0.8):
        executor.log("血量低，喝药水", "WARNING")
        executor.run_script("potion.yaml")
    else:
        # 普通攻击
        executor.click_image("attack_btn", 0.8)
    
    # 技能冷却延迟
    executor.delay(1000)
