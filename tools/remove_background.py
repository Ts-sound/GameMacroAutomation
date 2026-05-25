"""背景移除工具 - 使用 OpenCV GrabCut 算法"""
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import sys


def remove_background_opencv(image_path: str, output_path: str = None) -> np.ndarray:
    """使用 OpenCV GrabCut 算法移除背景

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（可选）

    Returns:
        移除背景后的 numpy 数组 (BGRA)
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")

    h, w = img.shape[:2]

    mask = np.zeros((h, w), np.uint8)

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    rect = (5, 5, w - 10, h - 10)

    cv2.grabCut(img, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)

    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")

    result = img.copy()
    result[mask2 == 0] = (255, 255, 255, 0)
    result[mask2 == 1] = (result[mask2 == 1, 0], result[mask2 == 1, 1], result[mask2 == 1, 2], 255)

    b, g, r = cv2.split(result)
    alpha = mask2 * 255
    result_rgba = cv2.merge((b, g, r, alpha))

    if output_path:
        cv2.imwrite(output_path, result_rgba)

    return result_rgba


def remove_background_color_key(image_path: str, output_path: str = None, tolerance: int = 30) -> np.ndarray:
    """使用颜色键（Color Key）移除背景 - 适用于纯色背景

    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（可选）
        tolerance: 颜色容差

    Returns:
        移除背景后的 numpy 数组 (RGBA)
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图片: {image_path}")

    h, w = img.shape[:2]

    top_left_color = img[0, 0]

    lower = np.array([max(0, c - tolerance) for c in top_left_color], dtype=np.uint8)
    upper = np.array([min(255, c + tolerance) for c in top_left_color], dtype=np.uint8)

    mask = cv2.inRange(img, lower, upper)
    mask = cv2.bitwise_not(mask)

    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    b, g, r = cv2.split(img)
    alpha = mask

    result_rgba = cv2.merge((b, g, r, alpha))

    if output_path:
        cv2.imwrite(output_path, result_rgba)

    return result_rgba


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python remove_background.py <图片路径> [输出路径] [方法]")
        print("方法: grabcut (默认) 或 colorkey")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    method = sys.argv[3] if len(sys.argv) > 3 else "grabcut"

    if method == "colorkey":
        result = remove_background_color_key(input_path, output_path)
    else:
        result = remove_background_opencv(input_path, output_path)

    print(f"背景移除完成: {output_path or '仅返回数组'}")