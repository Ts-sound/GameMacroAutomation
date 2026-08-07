"""ESP32 键盘控制示例

演示 Esp32Keyboard 模块的 tap / hold / combo 用法。
独立运行，不依赖图像检测。

运行前先修改 esp32_keyboard.py 中的 DEFAULT_HOST / DEFAULT_PORT
或在本文件顶部通过参数指定。

用法:
    python esp_keyboard_demo.py
"""

from esp32_keyboard import DEFAULT_HOST, DEFAULT_PORT, Esp32Keyboard


def main():
    kb = Esp32Keyboard(host=DEFAULT_HOST, port=DEFAULT_PORT)
    try:
        kb.connect()

        print("单击 ;")
        kb.tap(";", press_ms=50)

        print("长按 ; 500ms")
        kb.hold(";", duration_ms=500)

        print("组合键 ctrl+s")
        kb.combo(["ctrl", "s"])

        print("单击 空格")
        kb.tap("space", press_ms=50)
    finally:
        kb.close()


if __name__ == "__main__":
    main()
