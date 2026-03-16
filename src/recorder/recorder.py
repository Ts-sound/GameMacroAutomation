"""录制器模块 - 录制输入并生成 YAML 脚本"""
import time
import yaml
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from src.core.screen import ScreenManager, WindowInfo
from src.core.input import InputRecorder, RecordedAction
from src.core.config import MacroScript, ScriptMeta, ScriptConfig, ScriptAssets


class ScriptRecorder:
    """脚本录制器"""
    
    def __init__(self, output_dir: str = "scripts"):
        """
        Args:
            output_dir: 脚本输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.screen_manager = ScreenManager()
        self.input_recorder: Optional[InputRecorder] = None
        self.current_window: Optional[WindowInfo] = None
    
    def find_game_window(self, title: str) -> Optional[WindowInfo]:
        """
        查找游戏窗口
        
        Args:
            title: 窗口标题
        
        Returns:
            WindowInfo 或 None
        """
        return self.screen_manager.find_window(title)
    
    def start_recording(self, window_title: str) -> bool:
        """
        开始录制
        
        Args:
            window_title: 游戏窗口标题
        
        Returns:
            是否成功开始
        """
        self.current_window = self.find_game_window(window_title)
        if not self.current_window:
            print(f"未找到窗口：{window_title}")
            return False
        
        self.input_recorder = InputRecorder(self.screen_manager)
        self.input_recorder.start_recording()
        return True
    
    def stop_recording(self) -> List[RecordedAction]:
        """
        停止录制
        
        Returns:
            录制的动作列表
        """
        if not self.input_recorder:
            return []
        return self.input_recorder.stop_recording()
    
    def generate_script_name(self, base_name: str) -> str:
        """生成脚本名称"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}"
    
    def actions_to_yaml(self, actions: List[RecordedAction], window_title: str) -> dict:
        """
        将动作列表转换为 YAML 结构
        
        Args:
            actions: 录制的动作列表
            window_title: 窗口标题
        
        Returns:
            YAML 字典结构
        """
        # 构建动作序列
        yaml_actions = []
        
        for action in actions:
            if action.action_type == "mouse_click":
                yaml_actions.append({
                    "type": "click",
                    "x": action.x,
                    "y": action.y,
                    "button": action.button
                })
            elif action.action_type == "key_press":
                yaml_actions.append({
                    "type": "keypress",
                    "key": action.key
                })
        
        # 如果有时间间隔，添加 delay
        if len(actions) > 1:
            enhanced_actions = []
            for i, action in enumerate(yaml_actions):
                if i > 0:
                    # 计算与前一个动作的时间间隔
                    delay_ms = actions[i].timestamp - actions[i-1].timestamp
                    if delay_ms > 50:  # 大于 50ms 才添加 delay
                        enhanced_actions.append({"type": "delay", "ms": delay_ms})
                enhanced_actions.append(action)
            yaml_actions = enhanced_actions
        
        return {
            "meta": {
                "name": "录制脚本",
                "version": "1.0",
                "created_by": "recorder"
            },
            "config": {
                "window_title": window_title,
                "log_level": "INFO",
                "retry_times": 3
            },
            "assets": {
                "images": {}
            },
            "actions": yaml_actions
        }
    
    def save_script(self, yaml_data: dict, script_name: str) -> str:
        """
        保存脚本到文件
        
        Args:
            yaml_data: YAML 字典结构
            script_name: 脚本名称
        
        Returns:
            保存的文件路径
        """
        script_path = self.output_dir / f"{script_name}.yaml"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)
        
        return str(script_path)
    
    def record(self, window_title: str, output_name: str) -> str:
        """
        完整录制流程
        
        Args:
            window_title: 游戏窗口标题
            output_name: 输出脚本名称
        
        Returns:
            保存的文件路径
        """
        print(f"开始录制，窗口：{window_title}")
        print("按 Ctrl+C 停止录制...")
        
        if not self.start_recording(window_title):
            raise RuntimeError(f"无法找到窗口：{window_title}")
        
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        
        actions = self.stop_recording()
        print(f"录制完成，共 {len(actions)} 个动作")
        
        yaml_data = self.actions_to_yaml(actions, window_title)
        script_path = self.save_script(yaml_data, output_name)
        
        print(f"脚本已保存：{script_path}")
        return script_path


# CLI 辅助函数
def record_script(output: str, window: Optional[str] = None):
    """CLI: 录制脚本"""
    if not window:
        print("请使用 --window 指定游戏窗口标题")
        return
    
    recorder = ScriptRecorder()
    output_name = Path(output).stem
    output_dir = str(Path(output).parent)
    recorder.output_dir = Path(output_dir)
    
    recorder.record(window, output_name)
