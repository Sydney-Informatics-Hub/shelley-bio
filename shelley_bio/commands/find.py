"""Find command — look up a single tool by name."""

import re
from difflib import get_close_matches
from pathlib import Path

from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table

from ..search.rsec import RsecSource
from ..utils.cache import compute_version_entries, load_versions_from_cache
from ..utils.globals import LMOD_MODULES_PATH
from ..utils.render import print_find_hint, render_tool_table
from ..utils.style import ShelleyStyle, console


def find_tool_sync(tool_name: str) -> None:
    """Find a tool by name using RSEC + CVMFS cache (no MCP server needed)."""
    clean_name = re.sub(r"[:/].*$", "", tool_name).strip()
    query_lower = clean_name.lower()

    with ShelleyStyle.create_status(f"Searching for tool: {clean_name}") as _status:
        source = RsecSource().load()
        pairs = load_versions_from_cache(clean_name) or []

    meta = None
    for entry in source.entries:
        if (entry.get("id", "").lower() == query_lower or
                entry.get("name", "").lower() == query_lower):
            meta = entry
            break

    if meta and not pairs:
        meta_id = meta.get("id", "")
        if meta_id.lower() != query_lower:
            pairs = load_versions_from_cache(meta_id) or []

    found = meta is not None or bool(pairs)

    suggestions: list[tuple[str, str]] = []
    if not found:
        entry_map = {
            e["id"].lower(): (e.get("name") or e["id"], e.get("description") or "")
            for e in source.entries if e.get("id")
        }
        suggestions = [
            entry_map[m]
            for m in get_close_matches(query_lower, entry_map.keys(), n=8, cutoff=0.6)
        ]

    containers_payload = None
    if pairs:
        tool_id = meta.get("id", clean_name) if meta else clean_name
        unique_versions = compute_version_entries(tool_id, pairs)
        containers_payload = {
            "available": True,
            "recent_versions": unique_versions[:5],
            "total_versions": len(unique_versions),
            "install_command": f"shelley-bio build {tool_id}",
        }

    tool_payload = None
    if meta:
        tool_payload = {
            "id": meta.get("id", clean_name),
            "name": meta.get("name", clean_name),
            "description": meta.get("description") or "",
            "homepage": meta.get("homepage") or "",
            "operations": source._flatten_edam(meta.get("edam-operations")),
            "inputs": source._flatten_edam(meta.get("edam-inputs")),
            "outputs": source._flatten_edam(meta.get("edam-outputs")),
        }

    _render_find_tool({
        "query": clean_name,
        "found": found,
        "suggestions": suggestions,
        "tool": tool_payload,
        "containers": containers_payload,
    })


def _render_find_tool(payload: dict) -> None:
    """Render a find_tool result payload."""
    query = payload.get("query", "unknown")

    if not payload.get("found"):
        suggestions = payload.get("suggestions", [])
        if suggestions:
            render_tool_table(
                suggestions,
                f"[warning]No exact match for '[tool]{query}[/tool]'. Did you mean:[/warning]",
                border_style="warning",
            )
            print_find_hint()
        else:
            console.print(ShelleyStyle.create_error_panel(
                "Tool Not Found",
                f"No tool or container matching '{query}' was found.",
                "Try: shelley-bio search <description>",
            ))
        return

    tool = payload.get("tool")
    containers = payload.get("containers")

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

    lines.append("\n")

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

        if any(not e["buildable"] for e in containers["recent_versions"]):
            console.print(
                "[muted]Buildable ✗: Versions not in the shpc registry may still be built, "
                "but can take a few minutes longer. This is suited for users who need "
                "a specific older version for reproducibility.[/muted]"
            )

        console.print(Panel(
            f"To install the latest version of {title_name}, run:\n\n"
            f"[command]shelley-bio build {query}[/command]",
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
