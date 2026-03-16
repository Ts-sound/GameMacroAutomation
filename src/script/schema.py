"""YAML 脚本 Schema 定义"""
from typing import List, Optional, Any, Literal


# 动作类型定义
ACTION_TYPES = Literal[
    "click",
    "click_image",
    "keypress",
    "type_text",
    "delay",
    "wait_image",
    "wait_image_disappear",
    "move_mouse",
    "scroll",
    "log",
    "run_script",
    "conditional",
    "loop",
    "parallel",
    "sequence"
]


# 条件类型定义
CONDITION_TYPES = Literal[
    "image_exists",
    "image_not_exists",
    "timeout",
    "custom"
]


# Schema 验证规则
SCRIPT_SCHEMA = {
    "meta": {
        "required": True,
        "fields": {
            "name": {"type": str, "required": True},
            "version": {"type": str, "required": False},
            "description": {"type": str, "required": False},
            "created_by": {"type": str, "required": False}
        }
    },
    "config": {
        "required": False,
        "fields": {
            "window_title": {"type": str, "required": False},
            "log_level": {"type": str, "required": False},
            "retry_times": {"type": int, "required": False}
        }
    },
    "assets": {
        "required": False,
        "fields": {
            "images": {"type": dict, "required": False}
        }
    },
    "actions": {
        "required": False,
        "type": list
    },
    "lua_script": {
        "required": False,
        "type": str
    },
    "scripts": {
        "required": False,
        "type": dict
    },
    "detection_zones": {
        "required": False,
        "type": dict
    }
}
