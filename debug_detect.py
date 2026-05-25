"""调试脚本：测试图像检测"""
from PIL import ImageGrab
import pyautogui
from pathlib import Path

# 测试图片
test_dir = Path("docs/examples/03_icon_changed/images")
template_path = test_dir / "icon_before.png"

print(f"模板路径: {template_path}")
print(f"模板存在: {template_path.exists()}")

# 全屏截图
screenshot = ImageGrab.grab()
print(f"屏幕尺寸: {screenshot.size}")

# 直接用 pyautogui 检测
print("\n开始检测...")
try:
    location = pyautogui.locateCenterOnScreen(str(template_path), confidence=0.8)
    if location:
        x, y = location
        print(f"✓ 找到图标，位置: ({x}, {y})")
    else:
        print("✗ 未找到图标")
except Exception as e:
    print(f"检测失败: {e}")

# 尝试降低置信度
print("\n尝试低置信度 (0.5)...")
try:
    location = pyautogui.locateCenterOnScreen(str(template_path), confidence=0.5)
    if location:
        x, y = location
        print(f"✓ 找到图标，位置: ({x}, {y})")
    else:
        print("✗ 未找到图标")
except Exception as e:
    print(f"检测失败: {e}")