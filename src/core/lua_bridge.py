"""Python-Lua 桥接模块"""
import logging
from typing import Any, Callable, Optional
from lupa import LuaRuntime, LuaError


class LuaBridge:
    """Lua 桥接 - 提供 Python 函数给 Lua 调用"""
    
    def __init__(self):
        """初始化 Lua 运行时"""
        self.state = LuaRuntime()
        self._logger = logging.getLogger(__name__)
        self._registered_functions: dict[str, Callable] = {}
    
    def execute_string(self, lua_code: str) -> Any:
        """
        执行 Lua 代码字符串
        
        Args:
            lua_code: Lua 代码
        
        Returns:
            执行结果
        """
        try:
            return self.state.execute(lua_code)
        except LuaError as e:
            self._logger.error(f"Lua 执行错误：{e}")
            raise
    
    def execute_file(self, lua_file: str) -> Any:
        """
        执行 Lua 文件
        
        Args:
            lua_file: 文件路径
        
        Returns:
            执行结果
        """
        with open(lua_file, 'r', encoding='utf-8') as f:
            lua_code = f.read()
        return self.execute_string(lua_code)
    
    def register_function(self, name: str, func: Callable):
        """
        注册 Python 函数到 Lua 全局环境
        
        Args:
            name: Lua 中的函数名
            func: Python 函数
        """
        self.state.globals()[name] = func
        self._registered_functions[name] = func
    
    def register_functions(self, functions: dict[str, Callable]):
        """批量注册函数"""
        for name, func in functions.items():
            self.register_function(name, func)
    
    def call_function(self, func_name: str, *args) -> Any:
        """
        调用 Lua 中已定义的函数
        
        Args:
            func_name: 函数名
            *args: 函数参数
        
        Returns:
            函数返回值
        """
        lua_func = self.state.globals()[func_name]
        if lua_func is None:
            raise ValueError(f"Lua 函数 '{func_name}' 未定义")
        return lua_func(*args)
    
    def get_global(self, name: str) -> Any:
        """获取 Lua 全局变量"""
        return self.state.globals()[name]
    
    def set_global(self, name: str, value: Any):
        """设置 Lua 全局变量"""
        self.state.globals()[name] = value
    
    def reset(self):
        """重置 Lua 状态"""
        self.state = LuaRuntime()
        self._registered_functions.clear()
