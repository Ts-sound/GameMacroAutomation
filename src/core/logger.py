"""日志系统模块"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ExecutionReport:
    """执行报告"""
    script: str
    start_time: str
    end_time: str = ""
    duration_seconds: float = 0.0
    status: str = "running"  # running/success/failed/stopped
    steps_total: int = 0
    steps_completed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    lua_logs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "script": self.script,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "steps_total": self.steps_total,
            "steps_completed": self.steps_completed,
            "errors": self.errors,
            "warnings": self.warnings,
            "lua_logs": self.lua_logs
        }
    
    def to_yaml(self) -> str:
        """转换为 YAML 字符串"""
        import yaml
        return yaml.dump(self.to_dict(), allow_unicode=True, default_flow_style=False)


class MacroLogger:
    """宏日志记录器"""
    
    def __init__(
        self,
        name: str = "gma",
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        log_console: bool = True
    ):
        """
        Args:
            name: 日志名称
            log_level: 日志等级
            log_file: 日志文件路径 (可选)
            log_console: 是否输出到控制台
        """
        self.name = name
        self.log_level = log_level
        self.log_file = log_file
        self.log_console = log_console
        
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, log_level.upper()))
        
        # 清除现有处理器
        self._logger.handlers.clear()
        
        # 控制台处理器
        if log_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '[%(levelname)s] %(asctime)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)
        
        # 执行报告
        self.report: Optional[ExecutionReport] = None
    
    def debug(self, message: str):
        """DEBUG 等级日志"""
        self._logger.debug(message)
    
    def info(self, message: str):
        """INFO 等级日志"""
        self._logger.info(message)
    
    def warning(self, message: str):
        """WARNING 等级日志"""
        self._logger.warning(message)
        if self.report:
            self.report.warnings.append(message)
    
    def error(self, message: str):
        """ERROR 等级日志"""
        self._logger.error(message)
        if self.report:
            self.report.errors.append(message)
    
    def start_execution(self, script_path: str):
        """开始执行"""
        self.report = ExecutionReport(
            script=script_path,
            start_time=datetime.now().isoformat()
        )
        self.info(f"开始执行脚本：{script_path}")
    
    def end_execution(self, status: str = "success"):
        """结束执行"""
        if self.report:
            self.report.end_time = datetime.now().isoformat()
            self.report.status = status
            
            start = datetime.fromisoformat(self.report.start_time)
            end = datetime.fromisoformat(self.report.end_time)
            self.report.duration_seconds = (end - start).total_seconds()
        
        self.info(f"执行结束：{status}")
    
    def step_start(self, step_name: str):
        """步骤开始"""
        self.info(f"执行步骤：{step_name}")
        if self.report:
            self.report.steps_total += 1
    
    def step_complete(self):
        """步骤完成"""
        if self.report:
            self.report.steps_completed += 1
    
    def save_report(self, output_path: str):
        """保存执行报告"""
        if not self.report:
            return
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.report.to_yaml())
        
        self.info(f"执行报告已保存：{output_path}")
    
    def get_report(self) -> Optional[ExecutionReport]:
        """获取执行报告"""
        return self.report


# 日志等级枚举
class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


# 创建日志的辅助函数
def create_logger(
    name: str = "gma",
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_console: bool = True
) -> MacroLogger:
    """
    创建日志记录器
    
    Args:
        name: 日志名称
        log_level: 日志等级
        log_file: 日志文件路径
        log_console: 是否输出到控制台
    
    Returns:
        MacroLogger 实例
    """
    return MacroLogger(name, log_level, log_file, log_console)
