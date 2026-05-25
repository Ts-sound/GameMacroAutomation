"""检查图片尺寸"""
from PIL import Image, ImageGrab

# 屏幕截图
screenshot = ImageGrab.grab()
print(f"屏幕尺寸: {screenshot.size}")

# 模板图片
template_path = "docs/examples/03_icon_changed/images/icon_before.png"
template = Image.open(template_path)
print(f"模板尺寸: {template.size}")

# 另一个模板
template_path2 = "docs/examples/03_icon_changed/images/icon_after.png"
template2 = Image.open(template_path2)
print(f"模板2尺寸: {template2.size}")