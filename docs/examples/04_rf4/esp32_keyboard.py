"""ESP32 BLE HID 键盘 TCP 客户端

通过 TCP JSON 协议 (v1.0) 控制 ESP32 BLE 键盘。
协议参考: /opt/tong/ws/git-repo/esp32-python-keyboard/README.md

支持:
- tap(key)     单击: press -> sleep(press_ms) -> release
- hold(key)    长按: press -> sleep(duration_ms) -> release
- combo(keys)  组合键: 依序按下修饰键+主键，依序释放
- press / release / release_all 原始控制

通信约定:
- 持久连接 + 自动重连
- 每个命令一次 sendall，然后读取完整 JSON 响应（ESP32 每次命令回复一个 JSON）
- 一次只发一个命令（ESP32 仅接受单客户端）
"""

import json
import logging
import socket
import threading
import time

DEFAULT_HOST = "192.168.137.11"
DEFAULT_PORT = 80
DEFAULT_PRESS_MS = 50
CONNECT_TIMEOUT = 5.0
RECV_TIMEOUT = 5.0
RETRY_TIMES = 2
RETRY_DELAY = 0.5


class Esp32KeyboardError(Exception):
    """ESP32 键盘通信错误"""


class Esp32Keyboard:
    """ESP32 键盘 TCP 客户端"""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        logger: logging.Logger = None,
        connect_timeout: float = CONNECT_TIMEOUT,
        recv_timeout: float = RECV_TIMEOUT,
    ):
        self.host = host
        self.port = port
        self.connect_timeout = connect_timeout
        self.recv_timeout = recv_timeout
        self._logger = logger or logging.getLogger("esp32_keyboard")
        self._sock: socket.socket = None
        self._lock = threading.Lock()

    def _log(self, level, message):
        self._logger.log(level, f"[ESP32] {message}")

    # ========== 连接管理 ==========

    def connect(self):
        """建立 TCP 连接（幂等：已有连接则忽略）"""
        if self._sock is not None:
            return
        try:
            sock = socket.create_connection(
                (self.host, self.port), timeout=self.connect_timeout
            )
            sock.settimeout(self.recv_timeout)
            self._sock = sock
            self._log(logging.INFO, f"已连接 {self.host}:{self.port}")
        except OSError as e:
            raise Esp32KeyboardError(f"连接失败 {self.host}:{self.port}: {e}") from e

    def close(self):
        """关闭连接"""
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def _ensure_connected(self):
        """确保连接可用，必要时重连"""
        if self._sock is None:
            self.connect()

    # ========== 底层命令 ==========

    def send_cmd(self, cmd: dict, retry: int = RETRY_TIMES) -> dict:
        """发送命令并读取响应

        Args:
            cmd: JSON 命令字典
            retry: 传输失败重试次数

        Returns:
            解析后的响应字典

        Raises:
            Esp32KeyboardError: 传输失败或响应解析失败
        """
        payload = json.dumps(cmd, separators=(",", ":")).encode("utf-8")

        for attempt in range(retry + 1):
            try:
                self._send_once(payload)
                return self._recv_response()
            except (OSError, socket.timeout, json.JSONDecodeError) as e:
                if attempt >= retry:
                    raise Esp32KeyboardError(
                        f"命令 {cmd.get('action')} 发送失败: {e}"
                    ) from e
                self._log(
                    logging.WARNING,
                    f"命令 {cmd.get('action')} 失败 ({e})，第 {attempt + 1} 次重试",
                )
                self.close()
                time.sleep(RETRY_DELAY)

    def _send_once(self, payload: bytes):
        with self._lock:
            self._ensure_connected()
            self._sock.sendall(payload)

    def _recv_response(self) -> dict:
        """读取完整 JSON 响应（阻塞直到解析成功或超时）"""
        buffer = b""
        deadline = time.time() + self.recv_timeout
        while True:
            remaining = deadline - time.time()
            if remaining <= 0:
                raise socket.timeout("等待响应超时")
            self._sock.settimeout(remaining)
            chunk = self._sock.recv(4096)
            if not chunk:
                raise OSError("连接被 ESP32 关闭")
            buffer += chunk
            try:
                return json.loads(buffer)
            except json.JSONDecodeError:
                continue

    def _check_response(self, cmd: dict, resp: dict):
        """校验响应，命令被拒绝时仅告警（不中断循环）"""
        if not isinstance(resp, dict) or not resp.get("success"):
            msg = resp.get("message", "unknown") if isinstance(resp, dict) else resp
            self._log(logging.WARNING, f"命令 {cmd.get('action')} 被拒绝: {msg}")

    # ========== 键盘操作 ==========

    def tap(self, key: str, press_ms: int = DEFAULT_PRESS_MS):
        """单击（短按）

        Args:
            key: 键名，如 ';'、'space'、'a'
            press_ms: 按下持续时间 ms
        """
        self.press(key)
        time.sleep(press_ms / 1000.0)
        self.release(key)

    def hold(self, key: str, duration_ms: int):
        """长按

        Args:
            key: 键名
            duration_ms: 按住时长 ms
        """
        self.press(key)
        time.sleep(duration_ms / 1000.0)
        self.release(key)

    def hold_interruptible(
        self,
        key: str,
        duration_ms: int,
        interrupt_check=None,
        interval_ms: int = 50,
    ):
        """可中断长按

        按住 key 期间周期调用 interrupt_check()，若返回非空（如触发区域名）
        立即释放并返回该值；否则按满 duration_ms 释放并返回 None。

        Args:
            key: 键名
            duration_ms: 最长按住时长 ms
            interrupt_check: 中断条件回调，返回非空值提前释放
            interval_ms: 条件检查间隔 ms

        Returns:
            中断触发值（如区域名），按满时长返回 None
        """
        self.press(key)
        fired = None
        deadline = time.time() + duration_ms / 1000.0
        while True:
            if interrupt_check is not None:
                fired = interrupt_check()
                if fired:
                    break
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            time.sleep(min(interval_ms / 1000.0, remaining))
        self.release(key)
        return fired

    def combo(self, keys, press_ms: int = DEFAULT_PRESS_MS):
        """组合键，如 ['ctrl', 's']

        Args:
            keys: 按键列表，修饰键在前
            press_ms: 同时按下持续时间 ms
        """
        for key in keys:
            self.press(key)
        time.sleep(press_ms / 1000.0)
        for key in reversed(keys):
            self.release(key)

    def press(self, key: str):
        """按下按键（不自动释放）"""
        resp = self.send_cmd(
            {"v": 1, "type": "keyboard", "action": "press", "params": {"keys": [key]}}
        )
        self._check_response({"action": "press"}, resp)

    def release(self, key: str):
        """释放按键"""
        resp = self.send_cmd(
            {
                "v": 1,
                "type": "keyboard",
                "action": "release",
                "params": {"keys": [key]},
            }
        )
        self._check_response({"action": "release"}, resp)

    def release_all(self):
        """释放所有按键"""
        resp = self.send_cmd(
            {"v": 1, "type": "keyboard", "action": "release_all", "params": {}}
        )
        self._check_response({"action": "release_all"}, resp)

    # ========== 上下文管理器 ==========

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
