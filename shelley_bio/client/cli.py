#!/usr/bin/env python3
"""
Shelley Bio CLI Client

Command-line client for querying the CVMFS-MCP server and building modules.
"""

import asyncio
import sys
import json
import re
from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from shelley_bio.utils.globals import LMOD_MODULES_PATH

from ..builder.cvmfs_builder import CVMFSModuleBuilder
from ..utils.style import (
    console, ShelleyStyle, print_banner, print_header, print_success,
    print_warning, print_error, print_info, print_rule, print_command
)


def _render_find_tool(payload: dict) -> None:
    """Render find_tool JSON payload using Rich components."""
    query = payload.get("query", "unknown")

    if not payload.get("found"):
        suggestions = payload.get("suggestions", [])
        if suggestions:
            table = Table(
                title=f"[warning]No exact match for '[tool]{query}[/tool]'. Did you mean:[/warning]",
                box=ROUNDED,
                border_style="warning",
                header_style="table.header",
                show_header=False,
            )
            table.add_column("Tool", style="tool", no_wrap=True)
            table.add_column("Command", style="command", no_wrap=True)
            for name in suggestions:
                table.add_row(name, f"shelley-bio find {name}")
            console.print(table)
        else:
            console.print(ShelleyStyle.create_error_panel(
                "Tool Not Found",
                f"No tool or container matching '{query}' was found.",
                "Try: shelley-bio search <description>",
            ))
        return

    tool = payload.get("tool")
    containers = payload.get("containers")

    # Tool info panel
    lines = []
    if tool:
        if tool.get("description"):
            lines.append(f"[header]Description[/header]\n[muted]{tool['description']}[/muted]\n")
        if tool.get("homepage"):
            lines.append(f"[header]Homepage[/header]    [info]{tool['homepage']}[/info]\n")
        if tool.get("operations"):
            lines.append(f"[header]Operations[/header]  [muted]{', '.join(tool['operations'])}[/muted]\n")
        if tool.get("inputs"):
            lines.append(f"[header]Inputs[/header]      [muted]{', '.join(tool['inputs'])}[/muted]\n")
        if tool.get("outputs"):
            lines.append(f"[header]Outputs[/header]     [muted]{', '.join(tool['outputs'])}[/muted]\n")

    title_name = tool.get("name") if tool else query
    console.print(Panel(
        "\n".join(lines) if lines else "[muted]No metadata available for this tool.[/muted]",
        title=f"[tool]{title_name}[/tool]",
        box=ROUNDED,
        border_style="primary",
        padding=(1, 2),
    ))

    lines.append('\n')

    if containers and containers.get("available"):
        lmod_path = Path(LMOD_MODULES_PATH)
        tool_id = tool.get("id", query) if tool else query

        table = Table(
            title="[header]Available Versions[/header]",
            box=ROUNDED,
            border_style="primary",
            header_style="table.header",
            show_lines=False,
        )
        table.add_column("Version", style="version", no_wrap=True)
        table.add_column("Buildable", no_wrap=True)
        table.add_column("Status", no_wrap=True)

        for entry in containers["recent_versions"]:
            version = entry["version"]
            buildable = entry["buildable"]
            installed = any((lmod_path / tool_id).glob(f"{version}*.lua"))
            buildable_str = "[success]✓[/success]" if buildable else "[muted]✗[/muted]"
            status = "[success]✓ installed[/success]" if installed else "[muted]not installed[/muted]"
            table.add_row(version, buildable_str, status)

        total = containers["total_versions"]
        shown = len(containers["recent_versions"])
        if total > shown:
            table.add_row(
                f"[muted]+ {total - shown} more[/muted]",
                "",
                f"[muted]shelley-bio versions {query}[/muted]",
            )

        console.print(table)

        console.print(Panel(
            f"To install the latest version of {title_name}, run:\n\n[command]shelley-bio build {query}[/command]",
            title="[header]Install[/header]",
            box=ROUNDED,
            border_style="info",
            padding=(0, 2),
        ))
    else:
        console.print(ShelleyStyle.create_warning_panel(
            "No Containers Available",
            "No Singularity containers found for this tool in CVMFS.",
        ))


async def query_tool(session: ClientSession, tool_name: str):
    """Query for a specific tool."""
    with ShelleyStyle.create_status(f"Searching for tool: {tool_name}") as status:
        result = await session.call_tool("find_tool", {"tool_name": tool_name})

    for content in result.content:
        if hasattr(content, 'text'):
            try:
                payload = json.loads(content.text)
                _render_find_tool(payload)
            except json.JSONDecodeError:
                console.print(content.text)


async def search_function(session: ClientSession, description: str, limit: int = 10):
    """Search by function/description."""
    with ShelleyStyle.create_status(f"Searching for: {description}") as status:
        result = await session.call_tool(
            "search_by_function",
            {"description": description, "limit": limit}
        )
    
    for content in result.content:
        if hasattr(content, 'text'):
            console.print(content.text)


async def list_tools(session: ClientSession, limit: int = 50):
    """List available tools."""
    with ShelleyStyle.create_status(f"Loading tools (limit: {limit})") as status:
        result = await session.call_tool(
            "list_available_tools",
            {"limit": limit}
        )
    
    for content in result.content:
        if hasattr(content, 'text'):
            console.print(content.text)


async def get_versions(session: ClientSession, tool_name: str):
    """Get available versions of a tool."""
    with ShelleyStyle.create_status(f"Getting versions for: {tool_name}") as status:
        result = await session.call_tool("get_container_versions", {"tool_name": tool_name})
    
    for content in result.content:
        if hasattr(content, 'text'):
            console.print(content.text)


def build_module(tool_spec: str) -> bool:
    """Build an Lmod module for a tool from CVMFS.
    
    Returns:
        bool: True if build was successful, False otherwise
    """
    import subprocess
    import os
    
    # Check if we need sudo (by testing write access to module directory)
    module_dir = Path("/apps/Modules/modulefiles")
    needs_sudo = not os.access(module_dir, os.W_OK) if module_dir.exists() else True
    
    if needs_sudo:
        # We need sudo - run the command with sudo automatically  
        script_dir = Path(__file__).parent.parent.parent
        shelley_bio_path = script_dir / "bin" / "shelley-bio"
        
        cmd = [
            "sudo", "-E", "env", f"PATH={os.environ['PATH']}", 
            str(shelley_bio_path), "build", tool_spec
        ]
        
        try:
            print_info(f"Running with elevated privileges: build {tool_spec}")
            result = subprocess.run(cmd, check=False)
            if result.returncode != 0:
                print_error(f"Build failed with exit code {result.returncode}")
                return False
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Build command failed: {e}")
            return False
        except KeyboardInterrupt:
            print_warning("Build cancelled by user")
            return False
    
    # Original build logic for when we already have permissions
    builder = CVMFSModuleBuilder()
        
    try:
        # Get available versions first for display
        if "/" in tool_spec:
            tool_name, requested_version = tool_spec.split("/", 1)
        elif ":" in tool_spec:
            tool_name, requested_version = tool_spec.split(":", 1)
        else:
            tool_name, requested_version = tool_spec, None
        
        # Resolve version (may prompt interactively — must run outside any Live/spinner context)
        final_tool, final_version = builder.search_tool_version(tool_name, requested_version)

        # Install via shpc (creates wrapper scripts + .lua module file)
        with ShelleyStyle.create_status(f"Building module for {tool_spec}") as status:
            module_file = builder.shpc_install(final_tool, final_version)
            available_versions = builder.list_versions(tool_name)
        
        # Display results
        if requested_version is None and len(available_versions) > 1:
            info_panel = ShelleyStyle.create_build_info(
                final_tool, final_version, available_versions
            )
            console.print(info_panel)
            print_rule()
        
        success_panel = ShelleyStyle.create_build_success(
            final_tool, final_version, module_file
        )
        console.print(success_panel)
        return True
        
    except Exception as e:
        # TODO: This doesn't capture all the errors accurately, e.g. errors in CVMFSModuleBuilder methods
        # TODO: Write unit test for e.g. build samtools:1.10293891 not found
        # Default message 
        title="Build Failed"
        msg=str(e)
        suggestion="Check that CVMFS is mounted and the tool exists"

        # Suppress generic suggestion for well-formed "not found" errors
        if re.search(r"^Version .* not found for", msg):
            suggestion=""

        error_panel = ShelleyStyle.create_error_panel(
            title=title,
            message=msg,
            suggestion=suggestion
        )
        console.print(error_panel)
        return False

def list_cvmfs_versions(tool_name: str) -> None:
    """List available versions of a tool in CVMFS."""
    builder = CVMFSModuleBuilder()
    
    try:
        with ShelleyStyle.create_status(f"Scanning CVMFS for {tool_name} versions") as status:
            version_path_pairs = builder.list_versions_with_paths(tool_name)
            
        if not version_path_pairs:
            error_panel = ShelleyStyle.create_error_panel(
                "No Versions Found",
                f"No versions of '{tool_name}' found in CVMFS",
                "Check the tool name spelling or try a different tool"
            )
            console.print(error_panel)
        else:
            versions_table = ShelleyStyle.create_versions_with_paths_table(tool_name, version_path_pairs)
            console.print(versions_table)
            
    except Exception as e:
        error_panel = ShelleyStyle.create_error_panel(
            "CVMFS Access Error",
            str(e),
            "Ensure CVMFS is mounted at /cvmfs/singularity.galaxyproject.org/"
        )
        console.print(error_panel)


async def interactive_mode(session: ClientSession):
    """Run in interactive mode."""
    console.clear()
    print_banner()
    
    # Create help table
    commands = [
        {"command": "find <tool>", "description": "Find information about a specific tool", "example": "find fastqc"},
        {"command": "search <description>", "description": "Search for tools by function", "example": "search quality control"},
        {"command": "versions <tool>", "description": "Get available container versions", "example": "versions samtools"},
        {"command": r"build <tool\[/ver]>", "description": "Build Lmod module for tool", "example": "build samtools/1.21"},
        {"command": "help", "description": "Show detailed help", "example": "help"},
        {"command": "exit", "description": "Exit interactive mode", "example": "exit"}
    ]
    
    help_table = ShelleyStyle.create_help_table(commands)
    console.print(help_table)
    print_rule()
    
    while True:
        try:
            user_input = console.input("\n[prompt]shelley-bio>[/prompt] ").strip()
            if not user_input:
                continue
                
            parts = user_input.split()
            command = parts[0].lower()
            
            if command in ["exit", "quit", "q"]:
                print_success("🐢 Goodbye!")
                break
                
            elif command == "help":
                console.print(help_table)
                console.print("\n")
                console.print(ShelleyStyle.format_command_examples())
                
            elif command == "find" and len(parts) > 1:
                await query_tool(session, parts[1])
                
            elif command == "find":
                print_warning("Missing tool name")
                print_info("Usage: [command]find <tool_name>[/command]")
                print_info("Example: [command]find fastqc[/command]")
                
            elif command == "search" and len(parts) > 1:
                description = " ".join(parts[1:])
                await search_function(session, description)
                
            elif command == "search":
                print_warning("Missing search terms")
                print_info("Usage: [command]search <description>[/command]")
                print_info("Example: [command]search quality control[/command]")
                
            elif command == "versions" and len(parts) > 1:
                await get_versions(session, parts[1])
                
            elif command == "versions":
                print_warning("Missing tool name")
                print_info("Usage: [command]versions <tool_name>[/command]")
                print_info("Example: [command]versions samtools[/command]")
                
            elif command == "build" and len(parts) > 1:
                if build_module(parts[1]):
                    print_success("Module built successfully! Exiting interactive mode.")
                    break
                    
            elif command == "build":
                print_warning("Missing tool specification")
                print_info("Usage: [command]build <tool_name>[/version][/command]")
                print_info("Examples:")
                print_info("  [command]build fastqc[/command]")
                print_info("  [command]build samtools/1.21[/command]")
                
            else:
                print_warning(f"Unknown command or missing arguments: '{command}'")
                print_info("Type [command]help[/command] for available commands")
        
        except KeyboardInterrupt:
            print_info("\nExiting interactive mode...")
            break
        except EOFError:
            print_info("\nExiting interactive mode...")
            break
        except Exception as e:
            print_error(f"Error: {e}")


async def _async_main() -> None:
    """Handle commands that require the MCP server."""
    command = sys.argv[1].lower()

    server_script = Path(__file__).parent.parent / "server" / "mcp_server.py"

    if not server_script.exists():
        error_panel = ShelleyStyle.create_error_panel(
            "Server Configuration Error",
            f"Server script not found at {server_script}",
            "Check Shelley Bio installation"
        )
        console.print(error_panel)
        sys.exit(1)
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python3",
        args=[str(server_script)],
        env=None
    )
    
    # Connect to server
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                
                if command == "find" and len(sys.argv) > 2:
                    await query_tool(session, sys.argv[2])
                
                elif command == "search" and len(sys.argv) > 2:
                    description = " ".join(sys.argv[2:])
                    await search_function(session, description)
                
                elif command == "versions" and len(sys.argv) > 2:
                    await get_versions(session, sys.argv[2])
                
                elif command == "interactive":
                    await interactive_mode(session)
                
                else:
                    error_panel = ShelleyStyle.create_error_panel(
                        "Unknown Command",
                        f"Unknown command: {command}",
                        "Use 'shelley-bio' with no arguments to see available commands"
                    )
                    console.print(error_panel)
                    sys.exit(1)
                    
    except Exception as e:
        error_panel = ShelleyStyle.create_error_panel(
            "Connection Error",
            f"Failed to run shelly-bio: {e}",
            "Check that all dependencies are installed"
        )
        console.print(error_panel)
        sys.exit(1)


def main() -> None:
    """CLI entry point. Sync commands are handled here before entering the event loop."""
    if len(sys.argv) < 2:
        console.clear()
        print_banner()
        print_rule("Command Usage", "secondary")

        usage_commands = [
            {"command": "find <tool_name>", "description": "Find information about a specific tool", "example": "shelley-bio find fastqc"},
            {"command": "search <description>", "description": "Search for tools by function", "example": "shelley-bio search 'quality control'"},
            {"command": "versions <tool_name>", "description": "Get available container versions", "example": "shelley-bio versions samtools"},
            {"command": r"build <tool\[/version\]>", "description": "Build Lmod module for tool", "example": "shelley-bio build samtools/1.21"},
            {"command": "interactive", "description": "Start interactive mode", "example": "shelley-bio interactive"}
        ]

        usage_table = ShelleyStyle.create_help_table(usage_commands)
        console.print(usage_table)
        console.print("\n")
        console.print(ShelleyStyle.format_command_examples())

        print_rule()
        print_info("For interactive mode with guided commands: [command]shelley-bio interactive[/command]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "build" and len(sys.argv) > 2:
        sys.exit(0 if build_module(sys.argv[2]) else 1)

    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
