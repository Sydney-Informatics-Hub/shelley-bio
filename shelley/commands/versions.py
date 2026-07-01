"""Versions command — list CVMFS container versions for a tool."""

from rich.box import ROUNDED
from rich.panel import Panel
from rich.table import Table

from ..utils.cache import compute_version_entries, load_versions_from_cache
from ..utils.render import paginate
from ..utils.style import ShelleyStyle, console


def versions_sync(tool_name: str) -> None:
    """List all container versions for a tool from the CVMFS cache."""
    with ShelleyStyle.create_status(f"Loading versions for: {tool_name}") as status:
        pairs = load_versions_from_cache(tool_name)

    if pairs is None:
        console.print(ShelleyStyle.create_error_panel(
            "Cache Not Found",
            "galaxy_singularity_cache.json.gz is missing.",
            "Run: shelley-build-cache",
        ))
        return

    if not pairs:
        console.print(ShelleyStyle.create_error_panel(
            "No Versions Found",
            f"No containers found for '{tool_name}'.",
            "Check the tool name spelling or try: shelley find " + tool_name,
        ))
        return

    entries = compute_version_entries(tool_name, pairs)

    def render_page(page_items, page, total_pages, total):
        _render_versions_page(page_items, page, total_pages, total, tool_name)

    paginate(entries, render_page)

    if any(not e["buildable"] for e in entries):
        console.print(
            "[muted]Buildable ✗: Versions not in the shpc registry may still be built, "
            "but can take a few minutes longer. This is suited for users who need "
            "a specific older version for reproducibility.[/muted]"
        )
    console.print(Panel(
        f"To install the latest version of {tool_name}, run:\n\n"
        f"[command]shelley build {tool_name}[/command]",
        title="[header]Install[/header]",
        box=ROUNDED,
        border_style="info",
        padding=(0, 2),
    ))


def _render_versions_page(
    entries: list[dict],
    page: int,
    total_pages: int,
    total: int,
    tool_name: str,
) -> None:
    """Render one page of versions with buildable status."""
    page_info = f" — page {page + 1} of {total_pages}" if total_pages > 1 else ""
    table = Table(
        title=f"[header]Available Versions for [tool]{tool_name}[/tool] ({total} total){page_info}[/header]",
        box=ROUNDED,
        border_style="primary",
        header_style="table.header",
        show_lines=False,
    )
    table.add_column("Version", style="version", no_wrap=True)
    table.add_column("Buildable", no_wrap=True)
    for entry in entries:
        buildable_str = "[success]✓[/success]" if entry["buildable"] else "[muted]✗[/muted]"
        table.add_row(entry["version"], buildable_str)
    console.print(table)
