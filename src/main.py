"""游戏宏自动化 - CLI 入口"""
import argparse
import sys


def cli():
    parser = argparse.ArgumentParser(
        description="游戏宏自动化系统",
        prog="gma"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # record 命令
    record_parser = subparsers.add_parser("record", help="录制宏脚本")
    record_parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出 YAML 文件路径"
    )
    record_parser.add_argument(
        "--window", "-w",
        help="游戏窗口标题 (可选，自动检测)"
    )
    record_parser.add_argument(
        "--screenshot-size", "-s",
        type=int,
        default=400,
        help="截图区域大小 (默认 400x400)"
    )
    
    # run 命令
    run_parser = subparsers.add_parser("run", help="运行宏脚本")
    run_parser.add_argument(
        "script",
        help="YAML 脚本文件路径"
    )
    run_parser.add_argument(
        "--window", "-w",
        help="游戏窗口标题 (覆盖脚本配置)"
    )
    run_parser.add_argument(
        "--log-level", "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志等级"
    )
    
    # capture-zone 命令
    capture_parser = subparsers.add_parser(
        "capture-zone",
        help="截图检测区域"
    )
    capture_parser.add_argument(
        "--output", "-o",
        required=True,
        help="输出图片路径"
    )
    
    # validate 命令
    validate_parser = subparsers.add_parser(
        "validate",
        help="验证脚本格式"
    )
    validate_parser.add_argument(
        "script",
        help="YAML 脚本文件路径"
    )
    
    # list 命令
    subparsers.add_parser("list", help="列出可用脚本")
    
    # tree 命令
    tree_parser = subparsers.add_parser(
        "tree",
        help="显示脚本依赖树"
    )
    tree_parser.add_argument(
        "script",
        help="YAML 脚本文件路径"
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    # 根据命令调用对应模块
    if args.command == "record":
        from src.recorder.recorder import record_script, list_windows
        if not args.window:
            list_windows()
            return
        record_script(args.output, args.window, args.screenshot_size)
    elif args.command == "run":
        from src.executor.executor import run_script
        run_script(args.script, args.window, args.log_level)
    elif args.command == "capture-zone":
        from src.tools.zone_captor import capture_zone
        capture_zone(args.output)
    elif args.command == "validate":
        from src.script.validator import validate_script_file
        validate_script_file(args.script)
    elif args.command == "list":
        from src.script.manager import list_scripts
        list_scripts()
    elif args.command == "tree":
        from src.script.manager import show_script_tree
        show_script_tree(args.script)


if __name__ == "__main__":
    cli()
