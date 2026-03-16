"""Python 脚本 API 封装"""
import time
import types
from pathlib import Path
from typing import Optional, Callable, Any


class ScriptAPI:
    """
    Python 脚本可用的 API 封装
    
    使用示例:
        def main(executor: ScriptAPI):
            executor.log("开始执行", "INFO")
            executor.click_image("attack_btn")
            
            executor.loop_while(
                lambda: executor.image_exists("boss_hp_bar"),
                lambda: (
                    executor.run_script("potion.yaml") 
                    if executor.image_exists("low_hp_warning")
                    else executor.click_image("attack_btn")
                ) or executor.delay(1000),
                max_iterations=100
            )
    """
    
    def __init__(self, script_executor):
        """
        Args:
            script_executor: ScriptExecutor 实例
        """
        self._executor = script_executor
        self.loop_count = 0  # 当前循环计数
    
    # ========== 图像识别 API ==========
    
    def click_image(self, name: str, confidence: float = 0.8):
        """点击图片"""
        self._executor._click_image(name, confidence, None)
    
    def image_exists(self, name: str, confidence: float = 0.8) -> bool:
        """检查图片是否存在"""
        return self._executor._image_exists(name, confidence)
    
    def wait_image(self, name: str, timeout: int = 5000) -> bool:
        """等待图片出现"""
        return self._executor._wait_image(name, timeout)
    
    # ========== 脚本控制 API ==========
    
    def run_script(self, name: str) -> bool:
        """运行子脚本"""
        return self._executor._run_sub_script(name)
    
    def delay(self, ms: int):
        """延迟"""
        self._executor.input_controller.delay(ms)
    
    def log(self, message: str, level: str = "INFO"):
        """日志"""
        self._executor.log(message, level)
    
    # ========== 循环控制 API ==========
    
    def loop_while(self, condition: Callable[[], bool], body: Callable[[], Any], 
                   max_iterations: int = 100, interval: int = 1000):
        """
        条件循环 - 当条件为 true 时持续执行
        
        Args:
            condition: 条件函数，返回 true 继续循环
            body: 循环体函数
            max_iterations: 最大循环次数
            interval: 每次循环间隔 (ms)
        """
        for i in range(max_iterations):
            self.loop_count = i + 1
            if not condition():
                self.log(f"循环结束：条件不满足 (第{i+1}次)", "DEBUG")
                break
            body()
            self.delay(interval)
        else:
            self.log(f"循环结束：达到最大次数 {max_iterations}", "WARNING")
        
        self.loop_count = 0
    
    def loop_times(self, count: int, body: Callable[[], Any], delay_ms: int = 0):
        """
        固定次数循环
        
        Args:
            count: 循环次数
            body: 循环体函数
            delay_ms: 每次循环间隔 (ms)
        """
        for i in range(count):
            self.loop_count = i + 1
            self.log(f"循环 {i+1}/{count}", "DEBUG")
            body()
            if delay_ms > 0:
                self.delay(delay_ms)
        
        self.loop_count = 0
    
    def loop_until(self, condition: Callable[[], bool], body: Callable[[], Any],
                   timeout: int = 30000, interval: int = 1000):
        """
        直到条件满足才停止的循环
        
        Args:
            condition: 停止条件函数，返回 true 停止循环
            body: 循环体函数
            timeout: 超时时间 (ms)
            interval: 条件检查间隔 (ms)
        """
        start_time = time.time()
        iterations = 0
        
        while True:
            self.loop_count = iterations + 1
            if condition():
                self.log(f"循环结束：条件满足 (第{iterations+1}次)", "DEBUG")
                break
            if (time.time() - start_time) * 1000 > timeout:
                self.log(f"循环结束：超时 {timeout}ms", "WARNING")
                break
            body()
            iterations += 1
            self.delay(interval)
        
        self.loop_count = 0


class PythonRunner:
    """Python 脚本加载器和执行器"""
    
    def __init__(self, script_executor):
        """
        Args:
            script_executor: ScriptExecutor 实例
        """
        self._executor = script_executor
        self._api = ScriptAPI(script_executor)
    
    def load_script(self, script_path: str) -> Optional[types.ModuleType]:
        """
        加载 Python 脚本为模块
        
        Args:
            script_path: 脚本路径
        
        Returns:
            加载的模块或 None
        """
        import importlib.util
        
        script_path = Path(script_path)
        if not script_path.exists():
            self._executor.log(f"Python 脚本不存在：{script_path}", "ERROR")
            return None
        
        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(
                "script_module", 
                str(script_path)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self._executor.log(f"Python 脚本加载成功：{script_path}", "DEBUG")
            return module
            
        except Exception as e:
            self._executor.log(f"Python 脚本加载失败：{e}", "ERROR")
            return None
    
    def execute(self, module: types.ModuleType) -> bool:
        """
        执行 Python 脚本的 main 函数
        
        Args:
            module: 已加载的模块
        
        Returns:
            执行是否成功
        """
        if not hasattr(module, 'main'):
            self._executor.log("错误：脚本缺少 main() 函数", "ERROR")
            return False
        
        try:
            # 调用 main(executor)
            result = module.main(self._api)
            return result is not False
            
        except Exception as e:
            self._executor.log(f"Python 脚本执行错误：{e}", "ERROR")
            import traceback
            self._executor.log(f"堆栈：{traceback.format_exc()}", "DEBUG")
            return False
