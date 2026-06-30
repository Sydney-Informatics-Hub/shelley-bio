"""Interactive command — guided REPL for shelley-bio."""

from .build import build_module
from .find import find_tool_sync
from .search import search_tools
from .versions import versions_sync
from ..utils.style import (
    console, ShelleyStyle, print_banner, print_rule,
    print_warning, print_info, print_success,
)

_COMMANDS = [
    {"command": "find <tool>",          "description": "Find information about a tool",     "example": "find fastqc"},
    {"command": "search <terms>",       "description": "Search for tools by description",   "example": "search quality control"},
    {"command": "versions <tool>",      "description": "List available container versions", "example": "versions samtools"},
    {"command": r"build <tool\[/ver]>", "description": "Build an Lmod module for a tool",   "example": "build samtools/1.21"},
    {"command": "help",                 "description": "Show this help table",              "example": "help"},
    {"command": "exit",                 "description": "Exit interactive mode",             "example": "exit"},
]


def interactive_mode() -> None:
    """Guided REPL — dispatches user input to command functions."""
    console.clear()
    print_banner()
    help_table = ShelleyStyle.create_help_table(_COMMANDS)
    console.print(help_table)
    print_rule()

    while True:
        try:
            raw = console.input("\n[prompt]shelley-bio>[/prompt] ").strip()
        except (KeyboardInterrupt, EOFError):
            print_info("\nExiting interactive mode...")
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd in ("exit", "quit", "q"):
            print_success("Goodbye!")
            break
        elif cmd == "help":
            console.print(help_table)
        elif cmd == "find":
            if len(parts) > 1:
                find_tool_sync(parts[1])
            else:
                print_warning("Usage: find <tool_name>")
        elif cmd == "search":
            if len(parts) > 1:
                search_tools(" ".join(parts[1:]))
            else:
                print_warning("Usage: search <description>")
        elif cmd == "versions":
            if len(parts) > 1:
                versions_sync(parts[1])
            else:
                print_warning("Usage: versions <tool_name>")
        elif cmd == "build":
            if len(parts) > 1:
                build_module(parts[1])
            else:
                print_warning("Usage: build <tool_name>[/version]")
        else:
            print_warning(f"Unknown command: '{cmd}'. Type help for usage.")
