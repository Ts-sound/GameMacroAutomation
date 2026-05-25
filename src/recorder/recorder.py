"""录制器模块 - 录制输入并生成 YAML 脚本"""
import time
import yaml
from pathlib import Path
from typing import Optional, List
from PIL import ImageGrab

from src.core.screen import ScreenManager
from src.core.input import InputRecorder, RecordedAction


class ScriptRecorder:
    """脚本录制器"""

    def __init__(self, output_dir: str = "scripts", screenshot_size: int = 400):
        """
        Args:
            output_dir: 脚本输出目录
            screenshot_size: 截图区域大小 (默认 400x400)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 图片保存目录（与脚本同目录下的 images 文件夹）
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self.screen_manager = ScreenManager()
        self.input_recorder: Optional[InputRecorder] = None

        # 截图配置
        self.screenshot_size = screenshot_size  # 截取点击位置周围区域大小
        self.click_counter = 0  # 点击计数器，用于生成唯一文件名

    def start_recording(self) -> bool:
        """开始录制"""
        self.click_counter = 0
        self.image_map = {}  # 动作索引 -> 截图文件名
        # 传入截图回调和停止回调，实现点击时实时截图和 F12 停止
        self.input_recorder = InputRecorder(
            self.screen_manager,
            on_click_callback=self._on_click_capture,
            on_stop_callback=self._on_stop_recording
        )
        self.input_recorder.start_recording()
        return True

    def _on_stop_recording(self):
        """停止录制回调（F12 触发）"""
        self.stop_recording()

    def _on_click_capture(self, x: int, y: int, button: str) -> Optional[str]:
        """
        点击回调函数 - 实时截图

        Args:
            x, y: 屏幕绝对坐标
            button: 鼠标按钮

        Returns:
            截图文件名
        """
        img_file = self._capture_screen_region(x, y)
        if img_file:
            # 记录动作索引和文件名的映射
            action_idx = len(self.input_recorder.actions)
            self.image_map[action_idx] = img_file
        return img_file

    def stop_recording(self) -> List[RecordedAction]:
        """停止录制"""
        if not self.input_recorder:
            return []
        return self.input_recorder.stop_recording()

    def _capture_screen_region(self, x: int, y: int) -> Optional[str]:
        """
        截取屏幕区域

        Args:
            x, y: 屏幕绝对坐标

        Returns:
            保存的图片文件名
        """
        half_size = self.screenshot_size // 2
        x1 = max(0, x - half_size)
        y1 = max(0, y - half_size)

        # 直接截取屏幕区域
        screenshot = ImageGrab.grab(bbox=(x1, y1, x1 + self.screenshot_size, y1 + self.screenshot_size))

        # 检查截图是否有效（不是全黑）
        import numpy as np
        img_array = np.array(screenshot)
        if img_array.mean() < 10:  # 平均亮度太低，可能是全黑
            print(f"警告：截图过暗，可能是无效区域 ({x}, {y})")
            # 创建一个白色提示图片
            from PIL import Image, ImageDraw
            screenshot = Image.new('RGB', (self.screenshot_size, self.screenshot_size), color='white')
            draw = ImageDraw.Draw(screenshot)
            draw.text((10, 40), f"Click at ({x},{y})", fill='black')

        self.click_counter += 1
        filename = f"click_{self.click_counter:03d}.png"
        filepath = self.images_dir / filename
        screenshot.save(str(filepath))

        return filename

    def actions_to_yaml(
        self,
        actions: List[RecordedAction],
        image_map: Optional[dict] = None
    ) -> dict:
        """
        将动作列表转换为 YAML 结构

        Args:
            actions: 录制的动作列表
            image_map: 动作索引到图片文件名的映射 {action_index: filename}

        Returns:
            YAML 字典结构
        """
        image_map = image_map or {}

        # 构建动作序列
        yaml_actions = []
        assets_images = {}

        for i, action in enumerate(actions):
            if action.action_type == "mouse_click":
                # 检查是否有对应的截图
                if i in image_map:
                    img_file = image_map[i]
                    # 使用文件名作为图片名（不含.png）
                    img_name = Path(img_file).stem
                    assets_images[img_name] = f"images/{img_file}"

                    # 存储屏幕绝对坐标作为 offset（执行时用于验证）
                    yaml_actions.append({
                        "type": "click_image",
                        "image": img_name,
                        "offset": [action.x, action.y]  # 存储屏幕坐标
                    })
                else:
                    # 没有截图，使用普通点击
                    yaml_actions.append({
                        "type": "click",
                        "x": action.x,
                        "y": action.y,
                        "button": action.button
                    })

            elif action.action_type == "mouse_scroll":
                # 滚轮动作
                yaml_actions.append({
                    "type": "scroll",
                    "x": action.x,
                    "y": action.y,
                    "clicks": 1 if action.button == "up" else -1
                })

            elif action.action_type == "key_press":
                if action.key:  # 忽略空按键
                    yaml_actions.append({
                        "type": "keypress",
                        "key": action.key
                    })

        # 添加时间间隔
        if len(actions) > 1:
            enhanced_actions = []
            for i, action in enumerate(yaml_actions):
                if i > 0:
                    # 找到对应的原始动作索引
                    orig_idx = i
                    if orig_idx < len(actions):
                        delay_ms = actions[orig_idx].timestamp - actions[orig_idx - 1].timestamp
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
                "log_level": "INFO",
                "retry_times": 3
            },
            "assets": {
                "images": assets_images
            },
            "actions": yaml_actions
        }

    def save_script(self, yaml_data: dict, script_name: str) -> str:
        """保存脚本到文件"""
        script_path = self.output_dir / f"{script_name}.yaml"

        with open(script_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)

        return str(script_path)

    def record(self, output_name: str) -> str:
        """
        完整录制流程

        Args:
            output_name: 输出脚本名称

        Returns:
            保存的文件路径
        """
        print(f"开始录制...")
        print(f"操作说明:")
        print(f"  - 所有点击操作将被录制并自动截图")
        print(f"  - 按 F12 停止录制")
        print(f"  - 按 Ctrl+C 强制退出")

        if not self.start_recording():
            raise RuntimeError("无法开始录制")

        # 等待录制停止（F12 或 Ctrl+C）
        try:
            while self.input_recorder and self.input_recorder.is_recording:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[录制] 检测到 Ctrl+C，强制退出...")
            if self.input_recorder:
                self.input_recorder.stop_recording()

        # 如果还没有停止，手动停止
        if self.input_recorder and self.input_recorder.is_recording:
            self.input_recorder.stop_recording()

        actions = self.input_recorder.actions if self.input_recorder else []
        print(f"\n录制完成，共 {len(actions)} 个动作")

        # 显示截图统计
        screenshot_count = len(self.image_map)
        if screenshot_count > 0:
            print(f"已保存 {screenshot_count} 张截图到：{self.images_dir}")
            for i, img_file in self.image_map.items():
                print(f"  点击 {i+1}: {img_file}")

        yaml_data = self.actions_to_yaml(actions, self.image_map)
        script_path = self.save_script(yaml_data, output_name)

        print(f"\n脚本已保存：{script_path}")
        print(f"图片已保存：{self.images_dir}")
        return script_path


# CLI 辅助函数
def list_windows():
    """CLI: 列出所有可用窗口（保留作为独立工具）"""
    import pygetwindow as gw

    windows = gw.getAllWindows()

    # 过滤空标题和过小的窗口
    valid_windows = [
        w for w in windows
        if w.title and w.width > 100 and w.height > 100
    ]

    # 按标题排序
    valid_windows.sort(key=lambda w: w.title.lower())

    print("\n" + "=" * 60)
    print("可用窗口列表")
    print("=" * 60)
    print()

    if not valid_windows:
        print("未找到符合条件的窗口")
        print("提示：最小窗口尺寸为 100x100")
    else:
        print(f"找到 {len(valid_windows)} 个窗口:\n")

        for i, w in enumerate(valid_windows, 1):
            print(f"  [{i:3d}] {w.title}")
            print(f"        位置：({w.left}, {w.top})  尺寸：{w.width}x{w.height}")

    print()


def record_script(output: str, screenshot_size: int = 400):
    """CLI: 录制脚本

    Args:
        output: 输出 YAML 文件路径
        screenshot_size: 截图区域大小 (默认 400x400)
    """
    recorder = ScriptRecorder(
        output_dir=str(Path(output).parent),
        screenshot_size=screenshot_size
    )
    output_name = Path(output).stem
    recorder.record(output_name)
