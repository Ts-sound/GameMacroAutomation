"""LuaBridge 模块测试"""
import pytest
from src.core.lua_bridge import LuaBridge


class TestLuaBridge:
    def test_lua_state_creation(self):
        """测试 Lua 状态创建"""
        bridge = LuaBridge()
        assert bridge.state is not None
    
    def test_execute_lua_string_arithmetic(self):
        """测试执行 Lua 算术表达式"""
        bridge = LuaBridge()
        result = bridge.execute_string("return 2 + 2")
        assert result == 4
    
    def test_execute_lua_string_table(self):
        """测试执行 Lua 表"""
        bridge = LuaBridge()
        result = bridge.execute_string("return {name='test', value=42}")
        assert result['name'] == 'test'
        assert result['value'] == 42
    
    def test_register_function(self):
        """测试注册 Python 函数到 Lua"""
        bridge = LuaBridge()
        
        def test_func(x):
            return x * 2
        
        bridge.register_function("test_func", test_func)
        result = bridge.execute_string("return test_func(5)")
        assert result == 10
    
    def test_register_multiple_functions(self):
        """测试注册多个函数"""
        bridge = LuaBridge()
        
        def add(a, b):
            return a + b
        
        def multiply(a, b):
            return a * b
        
        bridge.register_functions({"add": add, "multiply": multiply})
        
        result1 = bridge.execute_string("return add(3, 4)")
        result2 = bridge.execute_string("return multiply(3, 4)")
        
        assert result1 == 7
        assert result2 == 12
    
    def test_call_lua_function(self):
        """测试调用 Lua 函数"""
        bridge = LuaBridge()
        bridge.execute_string("""
            function add(a, b)
                return a + b
            end
        """)
        result = bridge.call_function("add", 3, 4)
        assert result == 7
    
    def test_get_set_global(self):
        """测试获取设置全局变量"""
        bridge = LuaBridge()
        bridge.set_global("my_var", 42)
        result = bridge.get_global("my_var")
        assert result == 42
    
    def test_reset(self):
        """测试重置 Lua 状态"""
        bridge = LuaBridge()
        bridge.set_global("test", 100)
        bridge.reset()
        
        # 重置后变量应该不存在
        result = bridge.get_global("test")
        assert result is None
