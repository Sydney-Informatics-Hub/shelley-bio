"""Allow `python -m shelley`, so a process can re-invoke *itself*.

The build path re-execs under sudo. Resolving a `shelley` launcher on PATH can pick a
different installation than the one currently running — a developer testing a checkout
with `uv run shelley build` would silently hand the privileged half of the build to a
system-wide install of an older shelley. Re-invoking as
`sys.executable -m shelley` makes that impossible.
"""

from .client.cli import main

if __name__ == "__main__":
    main()
