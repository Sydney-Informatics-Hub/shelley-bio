#!/usr/bin/env python3
"""
Batch Module Builder for Shelley Bio

Builds multiple Lmod modules for automated environments.
"""

import sys
import subprocess
import os
from pathlib import Path

from ..utils.style import (
    console, ShelleyStyle, print_banner, print_header, print_success, 
    print_warning, print_error, print_info, print_rule, print_command
)


def build_module_with_sudo(tool: str, shelley_bio_path: Path) -> bool:
    """Build a single module using sudo if needed."""
    with ShelleyStyle.create_status(f"Building module for: {tool}") as status:
        # Use the command we know works from testing
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
    """
    Build modules for multiple tools.
    
    Args:
        tools: List of tool names/specifications
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if not tools:
        console.clear()
        print_banner()
        print_rule("Batch Module Builder", "secondary")
        
        # Usage information
        usage_commands = [
            {"command": "shelley-bio-batch [tools...]", "description": "Build modules for multiple tools", "example": "shelley-bio-batch samtools"},
            {"command": "shelley-bio-batch tool1 tool2", "description": "Build modules for multiple tools", "example": "shelley-bio-batch samtools fastqc bowtie2"},
            {"command": "shelley-bio-batch tool/version", "description": "Build module for specific version", "example": "shelley-bio-batch samtools/1.22"}
        ]
        
        usage_table = ShelleyStyle.create_help_table(usage_commands)
        console.print(usage_table)
        
        info_panel = ShelleyStyle.create_info_panel(
            "Batch Builder Features",
            "• Build Lmod module files in /apps/Modules/modulefiles/\n• Use the latest version if no version specified\n• Handle sudo permissions automatically\n• Preserve Python environment for MCP dependencies"
        )
        console.print(info_panel)
        return 0

    console.clear()
    print_banner()
    print_header("Batch Module Builder", f"Building modules for {len(tools)} tools")
    
    # Create tools table
    from rich.table import Table
    tools_table = Table(
        title="[header]Tools to Build[/header]",
        box="rounded", 
        border_style="border",
        header_style="table.header"
    )
    tools_table.add_column("#", style="muted", width=4)
    tools_table.add_column("Tool", style="tool")
    tools_table.add_column("Status", style="muted")
    
    for i, tool in enumerate(tools, 1):
        tools_table.add_row(str(i), tool, "Pending")
    
    console.print(tools_table)
    print_rule()

    # Find shelley-bio executable
    shelley_bio_path = Path(__file__).parent.parent.parent / "bin" / "shelley-bio"
    if not shelley_bio_path.exists():
        error_panel = ShelleyStyle.create_error_panel(
            "Configuration Error",
            f"shelley-bio not found at {shelley_bio_path}",
            "Check Shelley Bio installation"
        )
        console.print(error_panel)
        return 1

    # Build modules for each tool specified
    success_count = 0
    total_count = len(tools)
    results = []

    for i, tool in enumerate(tools, 1):
        console.print(f"\n[header]Building {i}/{total_count}:[/header] [tool]{tool}[/tool]")
        
        if build_module_with_sudo(tool, shelley_bio_path):
            success_count += 1
            results.append((tool, True, "Success"))
        else:
            results.append((tool, False, "Failed"))

    # Results summary
    print_rule("Build Results")
    results_table = Table(
        title="[header]Build Summary[/header]",
        box="rounded",
        border_style="border", 
        header_style="table.header"
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
        success_panel = ShelleyStyle.create_info_panel(
            "All Modules Built Successfully! 🎉",
            f"Successfully built {success_count}/{total_count} modules.\n\nNext steps:\n• [command]module avail[/command] - See available modules\n• [command]module load <tool>/<version>[/command] - Load a module"
        )
        console.print(success_panel)
        return 0
    else:
        warning_panel = ShelleyStyle.create_warning_panel(
            "Some Modules Failed",
            f"Successfully built {success_count}/{total_count} modules. Check errors above for failed builds."
        )
        console.print(warning_panel)
        return 1


def main():
    """Entry point for the batch builder script."""
    tools = sys.argv[1:] if len(sys.argv) > 1 else []
    sys.exit(batch_build_modules(tools))


if __name__ == "__main__":
    main()