"""图像检测调试脚本 - 全屏检测指定图片，打印位置与置信度

用法:
    python detect_debug.py <图片路径> [--grayscale] [--confidence 0.8] [--once]

- 默认持续检测（0.5s 间隔），命中时打印位置与置信度
- --once: 只检测一次
- ctrl+c 退出

示例:
    python detect_debug.py images/01_ready.png
    python detect_debug.py images/02_on_fish.png --grayscale --confidence 0.7 --once
"""

import argparse
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageGrab


def match_fullscreen(template_path: str, confidence: float, grayscale: bool):
    """全屏模板匹配，返回 (x, y, score) 或 None"""
    tpl = Image.open(template_path).convert("RGB")
    screen = ImageGrab.grab().convert("RGB")

    screen_arr = np.asarray(screen)
    tpl_arr = np.asarray(tpl)
    if grayscale:
        screen_arr = cv2.cvtColor(screen_arr, cv2.COLOR_RGB2GRAY)
        tpl_arr = cv2.cvtColor(tpl_arr, cv2.COLOR_RGB2GRAY)
    else:
        screen_arr = cv2.cvtColor(screen_arr, cv2.COLOR_RGB2BGR)
        tpl_arr = cv2.cvtColor(tpl_arr, cv2.COLOR_RGB2BGR)

    th, tw = tpl_arr.shape[:2]
    sh, sw = screen_arr.shape[:2]
    if tw > sw or th > sh:
        print(f"[ERROR] 模板大于屏幕: 模板 {tw}x{th}, 屏幕 {sw}x{sh}")
        return None

    result = cv2.matchTemplate(screen_arr, tpl_arr, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < confidence:
        return None

    cx = max_loc[0] + tw // 2
    cy = max_loc[1] + th // 2
    return (cx, cy, float(max_val))


def main():
    parser = argparse.ArgumentParser(description="全屏检测图片并打印位置与置信度")
    parser.add_argument("image", help="模板图片路径")
    parser.add_argument("--grayscale", action="store_true", help="灰度匹配")
    parser.add_argument("--confidence", type=float, default=0.8,
                        help="置信度阈值 (默认 0.8)")
    parser.add_argument("--once", action="store_true", help="只检测一次")
    args = parser.parse_args()

    print(
        f"检测 {args.image} (confidence={args.confidence}, "
        f"grayscale={args.grayscale})"
    )

    try:
        while True:
            result = match_fullscreen(args.image, args.confidence, args.grayscale)
            if result:
                x, y, score = result
                print(f"[命中] ({x}, {y}) conf={score:.3f}")
                if args.once:
                    return 0
            else:
                print("[未命中]")
                if args.once:
                    return 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n退出")
        return 0


if __name__ == "__main__":
    sys.exit(main())
