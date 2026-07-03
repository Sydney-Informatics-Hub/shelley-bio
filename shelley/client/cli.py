#!/usr/bin/env python3
"""Shelley CLI entry point."""
#TODO: Add docstring to inform agent rules: this file should contain the
# direct command-line interface. Helper functions, and style/rendering 
# functions always end up here. They should not. These should be imported from
# the relevant modules.

import sys
from pathlib import Path

from ..commands.build import build_module
from ..commands.find import find_tool_sync
from ..commands.interactive import interactive_mode
from ..commands.search import search_tools
from ..utils.batch import batch_build_modules, read_tools_file
from ..utils.style import (
    console, ShelleyStyle, print_banner, print_warning, print_info, print_rule,
    print_version,
)



def _print_usage() -> None:
    console.clear()
    print_banner()
    print_rule("Command Usage", "secondary")

    usage_commands = [
        {"command": "find <tool_name> [-v]", "description": "Find a tool; -v lists all container versions", "example": "shelley find fastqc"},
        {"command": "search <description>", "description": "Search for tools by function", "example": "shelley search 'quality control'"},
        {"command": r"build <tool\[/version\]>", "description": "Build Lmod module for tool", "example": "shelley build samtools/1.21"},
        {"command": "interactive", "description": "Start interactive mode", "example": "shelley interactive"},
        {"command": "help", "description": "Show this help message", "example": "shelley help"},
    ]

    usage_table = ShelleyStyle.create_help_table(usage_commands)
    console.print(usage_table)
    console.print("\n")
    console.print(ShelleyStyle.format_command_examples())
    print_rule()


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        _print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command in ("help", "--help", "-h"):
        _print_usage()
        sys.exit(0)

    if command in ("--version", "-V"):
        print_version()
        sys.exit(0)

    if command == "build" and len(sys.argv) > 2:
        arg = sys.argv[2]
        p = Path(arg)
        if p.is_file():
            tools = read_tools_file(p)
            if not tools:
                print_warning(f"No tool specs found in '{arg}' (file is empty or all comments)")
                sys.exit(1)
            sys.exit(batch_build_modules(tools))
        sys.exit(0 if build_module(arg) else 1)

    if command == "find":
        args = sys.argv[2:]
        verbose = any(a in ("-v", "--verbose") for a in args)
        positional = [a for a in args if a not in ("-v", "--verbose")]
        if positional:
            find_tool_sync(positional[0], verbose=verbose)
        else:
            print_warning("Missing tool name")
            print_info("Usage: [command]shelley find <tool_name> [-v][/command]")
            print_info("Example: [command]shelley find fastqc[/command]")
        sys.exit(0)

    if command == "search":
        if len(sys.argv) > 2:
            search_tools(" ".join(sys.argv[2:]))
        else:
            print_warning("Missing search terms")
            print_info("Usage: [command]shelley search <description>[/command]")
            print_info("Example: [command]shelley search 'quality control'[/command]")
        sys.exit(0)

    if command == "interactive":
        interactive_mode()
        sys.exit(0)

    console.print(ShelleyStyle.create_error_panel(
        "Unknown Command",
        f"Unknown command: '{command}'",
        "Run shelley --help for usage",
    ))
    sys.exit(1)


if __name__ == "__main__":
    main()
