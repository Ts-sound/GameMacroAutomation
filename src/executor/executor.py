"""脚本执行器模块"""

import logging
import time
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

import pyautogui
from PIL import ImageGrab

from src.core.config import ConfigManager, MacroScript
from src.core.image import ImageMatcher, MatchResult
from src.core.input import InputController
from src.core.screen import ScreenManager
from src.core.sound import SoundNotifier
from src.executor.api import PythonRunner, ScriptAPI
from src.script.validator import ScriptValidator


class ScriptExecutor:
    """脚本执行器"""

    def __init__(self, scripts_dir: str = "scripts", assets_dir: str = "assets"):
        """
        Args:
            scripts_dir: 脚本目录
            assets_dir: 资源目录
        """
        self.scripts_dir = Path(scripts_dir)
        self.assets_dir = Path(assets_dir)

        self.config_manager = ConfigManager()
        self.validator = ScriptValidator(str(scripts_dir))

        self.screen_manager = ScreenManager()
        self.image_matcher = ImageMatcher()
        self.sound_notifier = SoundNotifier()
        self.input_controller: Optional[InputController] = None
        self.python_runner: Optional[PythonRunner] = None
        self.script_api: Optional[ScriptAPI] = None

        self._logger: Optional[logging.Logger] = None
        self.current_script_dir: Optional[Path] = None

    def setup_logging(self, log_level: str = "INFO", log_file: Optional[str] = None):
        """设置日志"""
        self._logger = logging.getLogger("executor")
        self._logger.setLevel(getattr(logging, log_level.upper()))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if self._logger:
            getattr(self._logger, level.lower())(message)
        else:
            print(f"[{level}] {message}")

    def load_script(self, yaml_path: str) -> MacroScript:
        """加载脚本"""
        return self.config_manager.load_script(yaml_path)

    def validate_script(self, yaml_path: str) -> tuple[bool, list]:
        """验证脚本"""
        return self.validator.validate_script_file(yaml_path)

    def setup(self):
        """初始化设置（全屏模式）"""
        self.input_controller = InputController(logger=self._logger)
        self.script_api = ScriptAPI(self)
        self.python_runner = PythonRunner(self)

    def _wait_image(
        self, name: str, timeout: int = 5000, confidence: float = 0.8
    ) -> bool:
        """等待图片出现"""
        import time

        img_path = self._resolve_image_path(name, self.current_script_dir)
        if not img_path:
            self.log(f"图片不存在：{name}", "ERROR")
            return False

        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            try:
                location = pyautogui.locateOnScreen(
                    str(img_path), confidence=confidence
                )
                if location:
                    self.log(f"找到图片：{name}", "DEBUG")
                    return True
            except Exception:
                pass
            time.sleep(0.1)

        self.log(f"等待超时：{name}", "WARNING")
        return False

    def _execute_python_script(self, python_script: str) -> bool:
        """执行 Python 脚本"""
        # 优先从当前脚本目录查找，其次从 scripts_dir 查找
        if self.current_script_dir:
            script_path = self.current_script_dir / python_script
            if script_path.exists():
                return self._run_python_script_file(script_path)

        # 回退到 scripts_dir
        script_path = self.scripts_dir / python_script
        if not script_path.exists():
            self.log(f"Python 脚本不存在：{python_script}", "ERROR")
            return False

        return self._run_python_script_file(script_path)

    def _run_python_script_file(self, script_path: Path) -> bool:
        """执行 Python 脚本文件"""
        self.log(f"执行 Python 脚本：{script_path}")
        try:
            module = self.python_runner.load_script(str(script_path))
            if module is None:
                return False
            return self.python_runner.execute(module)
        except Exception as e:
            self.log(f"Python 执行错误：{e}", "ERROR")
            return False

    def _click_image(self, name: str, confidence: float = 0.7, offset=None):
        """点击图片"""
        import time
        import traceback

        start_time = time.time()
        scaled_x, scaled_y = 0, 0  # Initialize fallback variables

        try:
            self.log(f"[识别] 开始识别：{name}", "DEBUG")

            img_path = self._resolve_image_path(name, self.current_script_dir)
            if img_path is None:
                self.log(f"[识别] 图片不存在：{name}", "ERROR")
                return

            self.log(f"[识别] 图片路径：{img_path}", "DEBUG")

            # 使用 pyautogui.locateCenterOnScreen 直接识别
            self.log(
                f"[识别] 使用 pyautogui.locateCenterOnScreen (confidence={confidence})",
                "DEBUG",
            )
            match_start = time.time()

            # 方法 1：直接在屏幕上查找
            location = pyautogui.locateCenterOnScreen(
                str(img_path), confidence=confidence
            )
            match_time = (time.time() - match_start) * 1000
            self.log(f"[识别] 匹配耗时：{match_time:.1f}ms", "DEBUG")

            if location:
                elapsed = (time.time() - start_time) * 1000
                x, y = location
                self.log(
                    f"[识别] ✓ 成功 | {name} | "
                    f"pos=({x},{y}) | "
                    f"耗时={elapsed:.1f}ms",
                    "INFO",
                )
                if self.input_controller:
                    # 图像识别返回的是屏幕实际坐标，直接点击
                    self.input_controller.click_with_move(x, y)
                self.log(f"[点击] ✓ 图像识别点击：{name} -> ({x}, {y})", "INFO")
                return

            # 尝试降低置信度
            self.log(
                f"[识别] 未找到匹配 (confidence={confidence})，尝试低阈值 (0.5)...",
                "DEBUG",
            )
            match_start = time.time()
            location = pyautogui.locateCenterOnScreen(str(img_path), confidence=0.5)
            match_time = (time.time() - match_start) * 1000

            if location:
                elapsed = (time.time() - start_time) * 1000
                x, y = location
                self.log(
                    f"[识别] ⚠ 低置信度 | {name} | "
                    f"pos=({x},{y}) | "
                    f"耗时={elapsed:.1f}ms",
                    "WARNING",
                )
                if self.input_controller:
                    # 图像识别返回的是屏幕实际坐标，直接点击
                    self.input_controller.click_with_move(x, y)
                self.log(f"[点击] ⚠ 低置信度点击：{name} -> ({x}, {y})", "WARNING")
                return

            self.log(f"[识别] ✗ 失败：{name} (未找到匹配)", "WARNING")

            # 图像识别失败，使用存储的屏幕坐标作为 fallback
            if offset is not None and len(offset) == 2:
                try:
                    screen_x, screen_y = int(offset[0]), int(offset[1])
                    if self.input_controller:
                        self.input_controller.click_with_move(screen_x, screen_y)
                    elapsed = (time.time() - start_time) * 1000
                    self.log(
                        f"[识别] → Fallback | {name} | "
                        f"pos=({screen_x},{screen_y}) | "
                        f"耗时={elapsed:.1f}ms",
                        "INFO",
                    )
                    self.log(
                        f"[点击] → Fallback 点击：{name} -> ({screen_x}, {screen_y})",
                        "INFO",
                    )
                    return
                except Exception as e:
                    self.log(f"[识别] Fallback 失败：{e}", "ERROR")

            self.log(f"[识别] ✗ 未找到图片：{name}", "ERROR")

        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            self.log(f"[识别] ✗ 异常：{e} (耗时={elapsed:.1f}ms)", "ERROR")
            self.log(f"堆栈：{traceback.format_exc()}", "DEBUG")
            raise

    def _image_exists(self, name: str, confidence: float = 0.8) -> bool:
        """检查图片是否存在"""
        img_path = self._resolve_image_path(name, self.current_script_dir)
        if not img_path:
            return False

        try:
            location = pyautogui.locateOnScreen(str(img_path), confidence=confidence)
            return location is not None
        except Exception:
            return False

    def _detect_in_region(
        self,
        region: dict,
        template_name: str,
        confidence: float = 0.8,
    ) -> List[MatchResult]:
        """区域检测 - 内部方法"""
        img_path = self._resolve_image_path(template_name, self.current_script_dir)
        if not img_path:
            self.log(f"图片不存在：{template_name}", "ERROR")
            return []

        template = self.image_matcher.load_template(str(img_path))
        if template is None:
            self.log(f"模板加载失败：{template_name}", "ERROR")
            return []

        screenshot = ImageGrab.grab()
        results = self.image_matcher.find_in_region(
            screenshot, template, region, confidence
        )
        self.log(f"区域检测 {template_name}：找到 {len(results)} 个匹配", "DEBUG")
        return results

    def _monitor_icon_state(
        self,
        region: dict,
        normal_template: str,
        changed_template: Union[str, List[str]],
        interval_ms: int = 2000,
        on_changed: Optional[Callable] = None,
        sound: Optional[dict] = None,
        timeout: Optional[int] = None,
        color_mode: str = "pixel",
        histogram_threshold: float = 0.7,
    ) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """监测图标状态 - 内部方法

        持续循环检测，返回状态：
        - "none": 未检测到任何图标
        - "normal": 检测到原始 icon
        - "changed": icon 已变化

        当状态变为 "changed" 时，触发回调和声音，返回 (True, (x, y))
        超时或出错返回 (False, None)

        Args:
            color_mode: "pixel" 使用模板匹配，"histogram" 使用直方图比较
            histogram_threshold: histogram 模式下的相似度阈值
        """
        if isinstance(changed_template, str):
            changed_template = [changed_template]

        normal_path = self._resolve_image_path(normal_template, self.current_script_dir)

        if not normal_path:
            self.log(f"正常态模板不存在：{normal_template}", "ERROR")
            return False, None

        changed_paths: List[Path] = []
        for tpl in changed_template:
            p = self._resolve_image_path(tpl, self.current_script_dir)
            if p:
                changed_paths.append(p)
            else:
                self.log(f"变化态模板不存在：{tpl}", "WARNING")

        if not changed_paths:
            self.log("所有变化态模板均不存在", "ERROR")
            return False, None

        changed_names = ", ".join(changed_template)
        self.log(
            f"开始监测图标状态：normal={normal_template}, "
            f"changed=[{changed_names}], interval={interval_ms}ms, "
            f"color_mode={color_mode}",
            "INFO",
        )

        last_state: str = "normal"
        start_time = time.time()

        while True:
            if timeout is not None:
                elapsed_ms = (time.time() - start_time) * 1000
                if elapsed_ms >= timeout:
                    self.log(f"监测超时：{timeout}ms", "WARNING")
                    return False, None

            screenshot = ImageGrab.grab()

            if color_mode == "histogram":
                current_state, changed_coords = self._monitor_icon_state_histogram(
                    screenshot,
                    region,
                    normal_path,
                    changed_template,
                    changed_paths,
                    histogram_threshold,
                )
            else:
                current_state, changed_coords = self._monitor_icon_state_pixel(
                    screenshot,
                    region,
                    normal_template,
                    normal_path,
                    changed_template,
                    changed_paths,
                )

            if current_state == "changed" and last_state == "normal":
                self.log("[监测] 状态变化：normal -> changed，触发提示音！", "WARNING")
                if on_changed is not None:
                    try:
                        on_changed(current_state)
                    except Exception as e:
                        self.log(f"回调执行错误：{e}", "ERROR")
                if sound is not None:
                    self.sound_notifier.play(sound)
                return True, changed_coords

            last_state = current_state
            time.sleep(interval_ms / 1000.0)

    def _monitor_icon_state_pixel(
        self,
        screenshot,
        region: dict,
        normal_template: str,
        normal_path: Path,
        changed_template: List[str],
        changed_paths: List[Path],
    ) -> Tuple[str, Optional[Tuple[int, int]]]:
        """pixel 模式：基于模板匹配检测图标状态"""
        self.log(f"[监测] 截图尺寸: {screenshot.size}", "INFO")

        import pyautogui

        try:
            loc = pyautogui.locateCenterOnScreen(str(normal_path), confidence=0.8)
            self.log(f"[监测] pyautogui 直接检测: {loc}", "INFO")
        except Exception as e:
            self.log(f"[监测] pyautogui 检测失败: {e}", "ERROR")

        normal_matches = self.image_matcher.find_in_region(
            screenshot,
            str(normal_path),
            region,
            confidence=0.8,
        )

        changed_matches = []
        matched_template = None
        for tpl, tpl_path in zip(changed_template, changed_paths):
            matches = self.image_matcher.find_in_region(
                screenshot,
                str(tpl_path),
                region,
                confidence=0.8,
            )
            if matches:
                changed_matches = matches
                matched_template = tpl
                break

        match_info = (
            f"[监测] 匹配结果 - normal: {len(normal_matches)}, "
            f"changed: {len(changed_matches)}"
        )
        if matched_template:
            match_info += f" (matched: {matched_template})"
        self.log(match_info, "INFO")

        if normal_matches:
            self.log(
                f"[监测] 检测到 normal 图标，位置: "
                f"({normal_matches[0].screen_x}, {normal_matches[0].screen_y})",
                "INFO",
            )
            return "normal", None
        elif changed_matches:
            self.log(
                f"[监测] 检测到 changed 图标 ({matched_template})，"
                f"位置: ({changed_matches[0].screen_x}, "
                f"{changed_matches[0].screen_y})",
                "INFO",
            )
            return "changed", (
                changed_matches[0].screen_x,
                changed_matches[0].screen_y,
            )
        else:
            self.log("[监测] 未检测到任何图标", "INFO")
            return "none", None

    def _monitor_icon_state_histogram(
        self,
        screenshot,
        region: dict,
        normal_path: Path,
        changed_template: List[str],
        changed_paths: List[Path],
        histogram_threshold: float,
    ) -> Tuple[str, Optional[Tuple[int, int]]]:
        """histogram 模式：基于直方图相似度检测图标状态"""
        from PIL import Image

        rx = region.get("x", 0)
        ry = region.get("y", 0)
        rw = region.get("width", screenshot.width)
        rh = region.get("height", screenshot.height)

        sub_img = screenshot.crop((rx, ry, rx + rw, ry + rh))
        self.log(
            f"[监测-hist] 截取区域子图: ({rx},{ry},{rx+rw},{ry+rh}), "
            f"尺寸={sub_img.size}",
            "DEBUG",
        )

        normal_img = Image.open(str(normal_path)).convert("RGB")
        normal_img = normal_img.resize(sub_img.size, Image.Resampling.LANCZOS)

        try:
            similarity = self.image_matcher.compare_histogram(sub_img, normal_img)
        except ValueError as e:
            self.log(f"[监测-hist] 直方图计算失败: {e}", "ERROR")
            return "none", None

        self.log(
            f"[监测-hist] normal 相似度: {similarity:.4f} (阈值={histogram_threshold})",
            "INFO",
        )

        if similarity > histogram_threshold:
            self.log("[监测-hist] 检测到 normal 图标", "INFO")
            return "normal", None

        for tpl, tpl_path in zip(changed_template, changed_paths):
            changed_img = Image.open(str(tpl_path)).convert("RGB")
            changed_img = changed_img.resize(sub_img.size, Image.Resampling.LANCZOS)

            try:
                sim = self.image_matcher.compare_histogram(sub_img, changed_img)
            except ValueError as e:
                self.log(f"[监测-hist] changed 直方图计算失败 ({tpl}): {e}", "ERROR")
                continue

            self.log(
                f"[监测-hist] changed ({tpl}) 相似度: {sim:.4f} (阈值={histogram_threshold})",
                "INFO",
            )

            if sim > histogram_threshold:
                self.log(f"[监测-hist] 检测到 changed 图标 ({tpl})", "INFO")
                center_x = rx + rw // 2
                center_y = ry + rh // 2
                return "changed", (center_x, center_y)

        self.log("[监测-hist] 未检测到任何匹配图标", "INFO")
        return "none", None

    def _resolve_image_path(
        self, name: str, script_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """解析图片路径"""
        # 先在脚本目录的 images 文件夹中查找（录制器生成的图片）
        if script_dir:
            local_path = script_dir / "images" / f"{name}.png"
            if local_path.exists():
                return local_path

        # 再在 assets/templates 中查找
        template_path = self.assets_dir / "templates" / f"{name}.png"
        if template_path.exists():
            return template_path

        # 再在 assets/detection 中查找
        detection_path = self.assets_dir / "detection" / f"{name}.png"
        if detection_path.exists():
            return detection_path

        return None

    def _run_sub_script(self, script_name: str) -> bool:
        """运行子脚本"""
        script_path = self.scripts_dir / script_name
        if not script_path.exists():
            self.log(f"子脚本不存在：{script_name}", "ERROR")
            return False

        self.log(f"运行子脚本：{script_name}")
        return self.execute(str(script_path))

    def execute(self, yaml_path: str) -> bool:
        """
        执行脚本

        Args:
            yaml_path: YAML 脚本路径

        Returns:
            是否成功
        """
        self.log(f"开始执行脚本：{yaml_path}")

        # 验证脚本
        is_valid, errors = self.validate_script(yaml_path)
        if not is_valid:
            for error in errors:
                self.log(error, "ERROR")
            return False

        # 加载脚本
        script = self.load_script(yaml_path)
        self.log(f"脚本名称：{script.meta.name}")

        # 设置当前脚本目录（用于查找 images 文件夹）
        self.current_script_dir = Path(yaml_path).parent

        # 初始化（全屏模式）
        self.setup()

        if script.python_script:
            return self._execute_python_script(script.python_script)

        # 没有 Lua 脚本时，直接执行 actions 数组
        if script.actions:
            self.log(f"执行 {len(script.actions)} 个动作")
            result = self._execute_actions(script.actions, script.config.on_error)

            # 输出鼠标移动统计
            if self.input_controller:
                stats = self.input_controller.get_stats()
                self.log(
                    f"[统计] 鼠标移动：{stats.move_count}次 | "
                    f"总距离={stats.total_distance:.0f}px | "
                    f"总时长={stats.total_duration:.2f}s | "
                    f"平均速度={stats.avg_speed_pixels_per_second:.0f}px/s",
                    "INFO",
                )

            return result

        self.log("脚本执行完成")
        return True

    def _execute_actions(self, actions: list, on_error: str = "stop") -> bool:
        """执行动作列表"""
        for i, action in enumerate(actions):
            action_type = action.get("type")

            try:
                if action_type == "click_image":
                    img_name = action.get("image")
                    offset = action.get("offset")

                    # 调试信息
                    import numpy as np

                    self.log(
                        f"动作 {i+1}: click_image {img_name}, offset type={type(offset).__name__}, offset={offset}"
                    )

                    # 安全转换 offset 为列表
                    if offset is None:
                        offset_list = None
                    elif isinstance(offset, np.ndarray):
                        offset_list = offset.tolist()
                    else:
                        try:
                            offset_list = [int(v) for v in offset]
                        except (TypeError, ValueError) as e:
                            self.log(f"offset 转换失败：{e}", "WARNING")
                            offset_list = None

                    self._click_image(img_name, 0.8, offset_list)

                elif action_type == "click":
                    x = action.get("x", 0)
                    y = action.get("y", 0)
                    button = action.get("button", "left")
                    if self.input_controller:
                        self.input_controller.click(x, y, button)
                    self.log(f"点击 ({x}, {y}) {button}")

                elif action_type == "keypress":
                    key = action.get("key")
                    if key and self.input_controller:
                        self.input_controller.press(key)
                        self.log(f"按键：{key}")

                elif action_type == "scroll":
                    x = action.get("x", 0)
                    y = action.get("y", 0)
                    clicks = action.get("clicks", 1)
                    if self.input_controller:
                        self.input_controller.scroll(clicks, x, y)
                    self.log(f"滚轮：({x}, {y}) {clicks}")

                elif action_type == "delay":
                    ms = action.get("ms", 0)
                    if self.input_controller:
                        self.input_controller.delay(ms)

                elif action_type == "log":
                    msg = action.get("message", "")
                    level = action.get("level", "INFO")
                    self.log(msg, level)

                else:
                    self.log(f"未知动作类型：{action_type}", "WARNING")

                self.log(f"动作 {i+1}/{len(actions)} 完成：{action_type}")

            except Exception as e:
                self.log(f"动作 {i+1} 执行失败：{e}", "ERROR")
                if on_error == "stop":
                    return False

        return True


# CLI 辅助函数
def run_script(script_path: str, log_level: str = "INFO"):
    """CLI: 运行脚本"""
    executor = ScriptExecutor()
    executor.setup_logging(log_level)

    success = executor.execute(script_path)
    return 0 if success else 1
