
def main(executor):
    """
    主函数 - 脚本入口
    
    Args:
        executor: ScriptAPI 实例，提供所有可用的 API
    """
    executor.log("=== 战斗循环开始 ===", "INFO")
    
    if not executor.wait_image("screen_001", 10000):
        executor.log("screen_001 未出现，退出", "ERROR")
        return False
    
    attack_count = 0
    max_iterations = 3
    
    executor.log("开始循环...", "INFO")
    executor.loop_while(
        lambda: executor.image_exists("screen_001", 0.7),
        lambda: executor.run_script("test.yaml"),
        max_iterations,
        1000
    )