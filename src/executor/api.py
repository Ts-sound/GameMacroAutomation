"""Python 脚本 API 封装"""

import sys
import time
import types
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple, Union

from src.core.image import MatchResult


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

    # ========== 区域检测 API ==========

    def detect_in_region(
        self,
        region: dict,
        template_name: str,
        confidence: float = 0.8,
    ) -> List[MatchResult]:
        """
        在指定百分比区域内检测模板

        Args:
            region: 百分比区域 {"x": (x1, x2), "y": (y1, y2)}
            template_name: 模板名称（会通过 _resolve_image_path 解析）
            confidence: 置信度

        Returns:
            匹配结果列表
        """
        return self._executor._detect_in_region(region, template_name, confidence)

    def detect_in_center_region(
        self,
        center: tuple,
        size: tuple,
        template_name: str,
        confidence: float = 0.8,
        grayscale: bool = True,
    ) -> bool:
        """
        在指定中心点 + 尺寸区域内检测模板

        Args:
            center: 区域中心点 (x, y) 绝对像素
            size: 区域尺寸 (w, h) 绝对像素
            template_name: 模板名称
            confidence: 置信度
            grayscale: 是否灰度匹配

        Returns:
            bool: 是否找到匹配
        """
        matches = self._executor._detect_in_center_region(
            center, size, template_name, confidence, grayscale
        )
        return bool(matches)

    def locate_in_center_region(
        self,
        center: tuple,
        size: tuple,
        template_name: str,
        confidence: float = 0.8,
        grayscale: bool = True,
    ) -> Optional[Tuple[int, int]]:
        """
        在指定中心点 + 尺寸区域内检测模板并返回中心坐标

        Args:
            center: 区域中心点 (x, y) 绝对像素
            size: 区域尺寸 (w, h) 绝对像素
            template_name: 模板名称
            confidence: 置信度
            grayscale: 是否灰度匹配

        Returns:
            (x, y) 目标中心全屏坐标；未找到返回 None
        """
        matches = self._executor._detect_in_center_region(
            center, size, template_name, confidence, grayscale
        )
        if not matches:
            return None
        return (matches[0].screen_x, matches[0].screen_y)

    def get_detection_zones(self) -> dict:
        """获取当前脚本的检测区域配置（YAML detection_zones）"""
        script = getattr(self._executor, "current_script", None)
        return script.detection_zones if script else {}

    def get_script_config(self) -> dict:
        """获取当前脚本的 config 原始字典（YAML config 段）"""
        script = getattr(self._executor, "current_script", None)
        if script is None:
            return {}
        return script.raw_data.get("config", {}) or {}

    def monitor_icon_state(
        self,
        region: dict,
        normal_template: str,
        changed_template: Union[str, List[str]],
        interval_ms: int = 2000,
        on_changed: Optional[Callable[[str], None]] = None,
        sound: Optional[dict] = None,
        timeout: Optional[int] = None,
        color_mode: str = "template",
        histogram_threshold: float = 0.7,
        color_diff_threshold: float = 0.15,
    ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """
        监测图标状态变化

        持续循环检测，返回状态：
        - (True, (x, y)): icon 已变化，返回变化图标的全屏坐标
        - (False, None): 超时或未检测到变化

        每次循环检测返回：
        - "none": 未检测到任何图标
        - "normal": 检测到原始 icon
        - "changed": icon 已变化

        Args:
            region: 百分比区域 {"x": (x1, x2), "y": (y1, y2)}
            normal_template: 正常态模板名
            changed_template: 变化态模板名，支持单个模板名或模板名列表
            interval_ms: 检测间隔 (ms)，默认 2000ms
            on_changed: 回调函数，参数为 "normal" 或 "changed"
            sound: 声音配置 {"type": "system"} 或 {"type": "file", "file": "x.wav"}
            timeout: 超时时间 (ms)，None 表示无限
            color_mode: 颜色模式，"template"（模板匹配）或 "histogram"（直方图比较），
                默认 "template"
            histogram_threshold: 直方图比较阈值，仅 color_mode="histogram" 时生效，
                值越大要求越严格，默认 0.7

        Returns:
            (bool, tuple): (是否检测到变化, 变化图标的全屏坐标)
        """
        return self._executor._monitor_icon_state(
            region,
            normal_template,
            changed_template,
            interval_ms,
            on_changed,
            sound,
            timeout,
            color_mode=color_mode,
            histogram_threshold=histogram_threshold,
            color_diff_threshold=color_diff_threshold,
        )

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

    def loop_while(
        self,
        condition: Callable[[], bool],
        body: Callable[[], Any],
        max_iterations: int = 100,
        interval: int = 1000,
    ):
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

    def loop_until(
        self,
        condition: Callable[[], bool],
        body: Callable[[], Any],
        timeout: int = 30000,
        interval: int = 1000,
    ):
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
            # 将脚本所在目录加入 sys.path，支持导入同目录模块
            script_dir = str(script_path.parent)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)

            # 动态加载模块
            spec = importlib.util.spec_from_file_location(
                "script_module", str(script_path)
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
        if not hasattr(module, "main"):
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
