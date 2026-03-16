"""脚本执行器模块"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.core.config import ConfigManager, MacroScript, ScriptConfig
from src.core.screen import ScreenManager, WindowInfo
from src.core.image import ImageMatcher
from src.core.input import InputController
from src.core.lua_bridge import LuaBridge
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
        self.input_controller: Optional[InputController] = None
        self.lua_bridge: Optional[LuaBridge] = None
        
        self._logger: Optional[logging.Logger] = None
        self.current_window: Optional[WindowInfo] = None
        self.scale_factor: float = 1.0
        self.current_script_dir: Optional[Path] = None  # 当前脚本目录
    
    def setup_logging(self, log_level: str = "INFO", log_file: Optional[str] = None):
        """设置日志"""
        self._logger = logging.getLogger("executor")
        self._logger.setLevel(getattr(logging, log_level.upper()))
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
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
    
    def setup_window(self, window_title: str) -> bool:
        """
        设置游戏窗口
        
        Args:
            window_title: 窗口标题
        
        Returns:
            是否成功
        """
        self.current_window = self.screen_manager.find_window(window_title)
        if not self.current_window:
            self.log(f"未找到窗口：{window_title}", "ERROR")
            return False
        
        self.log(f"检测到窗口：{window_title} ({self.current_window.width}x{self.current_window.height})")
        return True
    
    def setup_scale_factor(self, reference_resolution: tuple[int, int] = (1920, 1080)):
        """设置缩放因子"""
        if self.current_window:
            current_size = (self.current_window.width, self.current_window.height)
            self.scale_factor = self.screen_manager.calculate_scale_factor(
                current_size, reference_resolution
            )
            self.log(f"自动计算缩放因子：{self.scale_factor:.2f}")
        
        self.input_controller = InputController(scale_factor=self.scale_factor)
    
    def setup_lua_bridge(self, script: MacroScript):
        """设置 Lua 桥接"""
        self.lua_bridge = LuaBridge()
        
        # 注册 Lua API
        self._register_lua_api(script)
    
    def _register_lua_api(self, script: MacroScript):
        """注册 Lua API 函数"""
        if not self.lua_bridge:
            return
        
        # 注册 wait_image
        def wait_image(name: str, timeout: int = 5000) -> bool:
            return self._wait_image(name, timeout)
        
        # 注册 click_image
        def click_image(name: str, confidence: float = 0.9, offset_x: int = 0, offset_y: int = 0):
            self._click_image(name, confidence, (offset_x, offset_y))
        
        # 注册 image_exists
        def image_exists(name: str, confidence: float = 0.8) -> bool:
            return self._image_exists(name, confidence)
        
        # 注册 run_script
        def run_script(script_name: str) -> bool:
            return self._run_sub_script(script_name)
        
        # 注册 delay
        def delay(ms: int):
            self.input_controller.delay(ms)
        
        # 注册 log
        def log_message(message: str, level: str = "INFO"):
            self.log(message, level)
        
        self.lua_bridge.register_functions({
            "wait_image": wait_image,
            "click_image": click_image,
            "image_exists": image_exists,
            "run_script": run_script,
            "delay": delay,
            "log": log_message
        })
    
    def _wait_image(self, name: str, timeout: int = 5000) -> bool:
        """等待图片出现"""
        import time
        
        img_path = self._resolve_image_path(name)
        if not img_path:
            self.log(f"图片不存在：{name}", "ERROR")
            return False
        
        template = self.image_matcher.load_template(str(img_path))
        if not template:
            self.log(f"无法加载图片：{name}", "ERROR")
            return False
        
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            if self.current_window:
                screen = self.screen_manager.get_screen_region(
                    self.current_window, 0, 0, 
                    self.current_window.width, self.current_window.height
                )
                result = self.image_matcher.find_template(screen, template)
                if result:
                    self.log(f"找到图片：{name} (confidence={result.confidence:.2f})")
                    return True
            
            time.sleep(0.1)
        
        self.log(f"等待超时：{name}", "WARNING")
        return False
    
    def _click_image(self, name: str, confidence: float = 0.9, offset: tuple[int, int] = (0, 0)):
        """点击图片"""
        img_path = self._resolve_image_path(name, self.current_script_dir)
        if not img_path:
            self.log(f"图片不存在：{name}", "ERROR")
            return
        
        template = self.image_matcher.load_template(str(img_path))
        if not template:
            self.log(f"无法加载图片：{name}", "ERROR")
            return
        
        if self.current_window:
            screen = self.screen_manager.get_screen_region(
                self.current_window, 0, 0,
                self.current_window.width, self.current_window.height
            )
            result = self.image_matcher.find_template(screen, template, confidence)
            
            if result:
                x = result.center[0] + offset[0]
                y = result.center[1] + offset[1]
                self.input_controller.click(x, y)
                self.log(f"点击图片：{name} ({x}, {y})")
            else:
                self.log(f"未找到图片：{name}", "ERROR")
    
    def _image_exists(self, name: str, confidence: float = 0.8) -> bool:
        """检查图片是否存在"""
        img_path = self._resolve_image_path(name)
        if not img_path:
            return False
        
        template = self.image_matcher.load_template(str(img_path))
        if not template:
            return False
        
        if self.current_window:
            screen = self.screen_manager.get_screen_region(
                self.current_window, 0, 0,
                self.current_window.width, self.current_window.height
            )
            result = self.image_matcher.find_template(screen, template, confidence)
            return result is not None
        
        return False
    
    def _resolve_image_path(self, name: str, script_dir: Optional[Path] = None) -> Optional[Path]:
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
        
        # 设置窗口
        if script.config.window_title:
            if not self.setup_window(script.config.window_title):
                return False
            self.setup_scale_factor(script.config.reference_resolution)
        
        # 如果有 Lua 脚本，执行 Lua
        if script.lua_script:
            lua_path = self.scripts_dir / script.lua_script
            if lua_path.exists():
                self.setup_lua_bridge(script)
                self.log(f"执行 Lua 脚本：{script.lua_script}")
                try:
                    result = self.lua_bridge.execute_file(str(lua_path))
                    return result is not False
                except Exception as e:
                    self.log(f"Lua 执行错误：{e}", "ERROR")
                    return False
            else:
                self.log(f"Lua 脚本不存在：{script.lua_script}", "ERROR")
                return False
        
        # 没有 Lua 脚本时，直接执行 actions 数组
        if script.actions:
            self.log(f"执行 {len(script.actions)} 个动作")
            return self._execute_actions(script.actions, script.config.on_error)
        
        self.log("脚本执行完成")
        return True
    
    def _execute_actions(self, actions: list, on_error: str = "stop") -> bool:
        """
        执行动作列表
        
        Args:
            actions: 动作列表
            on_error: 错误处理策略
        
        Returns:
            是否成功
        """
        for i, action in enumerate(actions):
            action_type = action.get("type")
            
            try:
                if action_type == "click_image":
                    img_name = action.get("image")
                    offset = action.get("offset", [0, 0])
                    self._click_image(img_name, 0.8, tuple(offset))
                
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
def run_script(script_path: str, window: Optional[str] = None, log_level: str = "INFO"):
    """CLI: 运行脚本"""
    executor = ScriptExecutor()
    executor.setup_logging(log_level)
    
    # 如果指定了窗口，覆盖脚本配置
    if window:
        script = executor.load_script(script_path)
        script.config.window_title = window
    
    success = executor.execute(script_path)
    return 0 if success else 1
