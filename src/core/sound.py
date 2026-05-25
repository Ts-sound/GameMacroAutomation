"""声音提醒模块"""
import logging
import platform
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("gma.sound")


class SoundNotifier:
    """声音提醒器"""

    def __init__(self):
        self._is_windows = platform.system() == "Windows"
        self._playsound_available = self._check_playsound()

    def _check_playsound(self) -> bool:
        try:
            import playsound
            return True
        except ImportError:
            return False

    def play_system_sound(self) -> bool:
        """播放 Windows 系统提示音"""
        if not self._is_windows:
            logger.warning("System sound only supported on Windows")
            try:
                sys.stdout.write("\a")
                sys.stdout.flush()
                return True
            except Exception:
                return False

        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return True
        except Exception as e:
            logger.error(f"Failed to play system sound: {e}")
            return False

    def play_file(self, file_path: str) -> bool:
        """
        播放指定音频文件

        Args:
            file_path: 音频文件路径 (.wav, .mp3)

        Returns:
            是否成功播放
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Sound file not found: {file_path}")
            return False

        if self._is_windows:
            try:
                import winsound
                suffix = path.suffix.lower()
                if suffix == ".wav":
                    winsound.PlaySound(str(path), winsound.SND_FILENAME)
                    return True
            except Exception as e:
                logger.debug(f"winsound playback failed: {e}")

        if self._playsound_available:
            try:
                from playsound import playsound as _playsound
                _playsound(str(path))
                return True
            except Exception as e:
                logger.error(f"playsound playback failed: {e}")
                return False

        logger.error(
            "No audio playback available. Install playsound: pip install playsound"
        )
        return False

    def play(self, config: dict) -> bool:
        """
        根据配置播放声音

        Args:
            config: {"type": "system"} 或 {"type": "file", "file": "alert.wav"}

        Returns:
            是否成功播放
        """
        sound_type = config.get("type", "system")

        if sound_type == "system":
            return self.play_system_sound()
        elif sound_type == "file":
            file_path = config.get("file", "")
            if not file_path:
                logger.error("Sound config missing 'file' key")
                return False
            return self.play_file(file_path)
        else:
            logger.error(f"Unknown sound type: {sound_type}")
            return False
