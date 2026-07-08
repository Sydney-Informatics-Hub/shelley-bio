"""Interactive command — guided REPL for shelley."""

from .build import build_module
from .find import find_tool_sync
from .search import search_tools
from ..utils.args import parse_build_flags, parse_verbosity
from ..utils.commands import CORE_COMMANDS
from ..utils.style import (
    console, ShelleyStyle, print_banner, print_rule,
    print_warning, print_info, print_success,
)

_COMMANDS = CORE_COMMANDS + [
    {"command": "help", "description": "Show this help table",  "example": "help"},
    {"command": "exit", "description": "Exit interactive mode", "example": "exit"},
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
            verbosity, positional = parse_verbosity(parts[1:])
            if positional:
                find_tool_sync(positional[0], verbosity=verbosity)
            else:
                print_warning("Usage: find <tool_name> [-v|-vv]")
        elif cmd == "search":
            if len(parts) > 1:
                search_tools(" ".join(parts[1:]))
            else:
                print_warning("Usage: search <description>")
        elif cmd == "build":
            edit_aliases, positional = parse_build_flags(parts[1:])
            if positional:
                build_module(positional[0], edit_aliases=edit_aliases)
            else:
                print_warning("Usage: build <tool_name>[/version] [--edit-aliases]")
        else:
            print_warning(f"Unknown command: '{cmd}'. Type help for usage.")
