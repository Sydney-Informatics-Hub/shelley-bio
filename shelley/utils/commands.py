"""Shared command metadata for the CLI usage and interactive help tables.

Single source of truth so the two help tables can't drift. ``example`` is the
bare invocation (no ``shelley`` prefix); the CLI prepends it, the interactive
REPL uses it as-is.
"""

# Commands available in both the CLI and the interactive REPL.
CORE_COMMANDS = [
    {"command": "find <tool> [-v|-vv]",
     "description": "Find a tool; -v lists all versions, -vv adds CVMFS paths",
     "example": "find fastqc"},
    {"command": "search <description>",
     "description": "Search for tools by function",
     "example": "search quality control"},
    {"command": r"build <tool\[/version]> [--edit-aliases]",
     "description": "Build Lmod module for tool; --edit-aliases to edit aliased binaries",
     "example": "build samtools/1.21"},
]
