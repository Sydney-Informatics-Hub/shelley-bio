"""
Batch module building utilities.
"""

import os
import shutil
import subprocess
from pathlib import Path

from rich.box import ROUNDED
from rich.table import Table
from shelley_bio.client.cli import build_module
from .style import (
    console, ShelleyStyle, print_banner, print_header, print_success,
    print_error, print_rule, print_info
)

def build_module_with_sudo(tool: str, shelley_bio_path: Path) -> bool:
    """Build a single module via `sudo shelley-bio build <tool>`."""
    with ShelleyStyle.create_status(f"Building module for: {tool}"):
        cmd = [
            "sudo", "-E", "env", f"PATH={os.environ['PATH']}",
            str(shelley_bio_path), "build", tool
        ]
        try:
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)
            if result.returncode == 0:
                print_success(f"Successfully built module for [tool]{tool}[/tool]")
                return True
            else:
                print_error(f"Failed to build module for [tool]{tool}[/tool]")
                if result.stderr:
                    console.print(f"[muted]{result.stderr.strip()}[/muted]")
                return False
        except Exception as e:
            print_error(f"Error building module for [tool]{tool}[/tool]: {e}")
            return False


def batch_build_modules(tools: list[str]) -> int:
    """Build Lmod modules for multiple tools in sequence.

    Args:
        tools: Tool names/specifications (e.g. ``["samtools", "fastqc/0.12.1"]``).

    Returns:
        0 if all builds succeed, 1 if any fail.
    """
    if not tools:
        console.print(ShelleyStyle.create_info_panel(
            "No tools specified",
            "Pass a file of tool specs to build in batch:\n\n"
            "[command]shelley-bio build tools.txt[/command]",
        ))
        return 0

    console.clear()
    print_info(f"Building modules for {len(tools)} tools")

    tools_table = Table(
        title="[header]Tools to Build[/header]",
        box=ROUNDED,
        border_style="border",
        header_style="table.header",
    )
    tools_table.add_column("#", style="muted", width=4)
    tools_table.add_column("Tool", style="tool")
    tools_table.add_column("Status", style="muted")

    for i, tool in enumerate(tools, 1):
        tools_table.add_row(str(i), tool, "Pending")

    console.print(tools_table)
    print_rule()

    success_count = 0
    total_count = len(tools)
    results: list[tuple[str, bool, str]] = []

    for i, tool in enumerate(tools, 1):
        console.print(f"\n[header]Building {i}/{total_count}:[/header] [tool]{tool}[/tool]")
        if build_module(tool, shelley_bio_path):
            success_count += 1
            results.append((tool, True, "Success"))
        else:
            results.append((tool, False, "Failed"))

    print_rule("Build Results")
    results_table = Table(
        title="[header]Build Summary[/header]",
        box=ROUNDED,
        border_style="border",
        header_style="table.header",
    )
    results_table.add_column("Tool", style="tool")
    results_table.add_column("Status", justify="center")
    results_table.add_column("Result", style="muted")

    for tool, success, status in results:
        status_style = "status.success" if success else "status.error"
        icon = "✓" if success else "✗"
        results_table.add_row(tool, f"[{status_style}]{icon}[/{status_style}]", status)

    console.print(results_table)

    if success_count == total_count:
        console.print(ShelleyStyle.create_info_panel(
            "All Modules Built Successfully! 🎉",
            f"Successfully built {success_count}/{total_count} modules.\n\nNext steps:\n"
            "• [command]module avail[/command] - See available modules\n"
            "• [command]module load <tool>/<version>[/command] - Load a module",
        ))
        return 0

    console.print(ShelleyStyle.create_warning_panel(
        "Some Modules Failed",
        f"Successfully built {success_count}/{total_count} modules. "
        "Check errors above for failed builds.",
    ))
    return 1
