#!/usr/bin/env python3
"""Shelley Bio CLI entry point."""
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
from ..commands.versions import versions_sync
from ..utils.batch import batch_build_modules, read_tools_file
from ..utils.style import (
    console, ShelleyStyle, print_banner, print_warning, print_info, print_rule,
)



def _print_usage() -> None:
    console.clear()
    print_banner()
    print_rule("Command Usage", "secondary")

    usage_commands = [
        {"command": "find <tool_name>", "description": "Find information about a specific tool", "example": "shelley-bio find fastqc"},
        {"command": "search <description>", "description": "Search for tools by function", "example": "shelley-bio search 'quality control'"},
        {"command": "versions <tool_name>", "description": "Get available container versions", "example": "shelley-bio versions samtools"},
        {"command": r"build <tool\[/version\]>", "description": "Build Lmod module for tool", "example": "shelley-bio build samtools/1.21"},
        {"command": "interactive", "description": "Start interactive mode", "example": "shelley-bio interactive"},
        {"command": "help", "description": "Show this help message", "example": "shelley-bio help"},
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
        if len(sys.argv) > 2:
            find_tool_sync(sys.argv[2])
        else:
            print_warning("Missing tool name")
            print_info("Usage: [command]shelley-bio find <tool_name>[/command]")
            print_info("Example: [command]shelley-bio find fastqc[/command]")
        sys.exit(0)

    if command == "search":
        if len(sys.argv) > 2:
            search_tools(" ".join(sys.argv[2:]))
        else:
            print_warning("Missing search terms")
            print_info("Usage: [command]shelley-bio search <description>[/command]")
            print_info("Example: [command]shelley-bio search 'quality control'[/command]")
        sys.exit(0)

    if command == "versions":
        if len(sys.argv) > 2:
            versions_sync(sys.argv[2])
        else:
            print_warning("Missing tool name")
            print_info("Usage: [command]shelley-bio versions <tool_name>[/command]")
            print_info("Example: [command]shelley-bio versions samtools[/command]")
        sys.exit(0)

    if command == "interactive":
        interactive_mode()
        sys.exit(0)

    console.print(ShelleyStyle.create_error_panel(
        "Unknown Command",
        f"Unknown command: '{command}'",
        "Run shelley-bio --help for usage",
    ))
    sys.exit(1)


if __name__ == "__main__":
    main()
