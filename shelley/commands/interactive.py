"""Interactive command — guided REPL for shelley."""

from .build import build_module
from .find import find_tool_sync
from .search import search_tools
from ..utils.style import (
    console, ShelleyStyle, print_banner, print_rule,
    print_warning, print_info, print_success,
)

_COMMANDS = [
    {"command": "find <tool> [-v]",     "description": "Find a tool; -v lists all versions", "example": "find fastqc"},
    {"command": "search <terms>",       "description": "Search for tools by description",   "example": "search quality control"},
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
            raw = console.input("\n[prompt]shelley>[/prompt] ").strip()
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
            flags = parts[1:]
            verbose = any(p in ("-v", "--verbose") for p in flags)
            positional = [p for p in flags if p not in ("-v", "--verbose")]
            if positional:
                find_tool_sync(positional[0], verbose=verbose)
            else:
                print_warning("Usage: find <tool_name> [-v]")
        elif cmd == "search":
            if len(parts) > 1:
                search_tools(" ".join(parts[1:]))
            else:
                print_warning("Usage: search <description>")
        elif cmd == "build":
            if len(parts) > 1:
                build_module(parts[1])
            else:
                print_warning("Usage: build <tool_name>[/version]")
        else:
            print_warning(f"Unknown command: '{cmd}'. Type help for usage.")
