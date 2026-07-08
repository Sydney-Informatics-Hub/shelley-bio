"""Build command — install Lmod modules from CVMFS."""

import os
import re
import shutil
import subprocess
from pathlib import Path

from ..builder.cvmfs_builder import CVMFSModuleBuilder
from ..utils.style import (
    console, ShelleyStyle, print_info, print_warning, print_error, print_rule,
)


def resolve_shelley_executable() -> str | None:
    """Locate the installed `shelley` launcher on PATH.

    Used to re-invoke ourselves under sudo. We rely on PATH rather than deriving
    a path from __file__, because the launcher and the package live in unrelated
    directories under a `uv tool install` layout (the launcher is in
    .../uv/tools/shelley/bin/, the package in .../site-packages/shelley/).
    """
    return shutil.which("shelley")


def build_module(tool_spec: str, edit_aliases: bool = False) -> bool:
    """Build an Lmod module for a tool from CVMFS.

    ``edit_aliases`` opens an interactive editor to deselect, rename, and add the
    aliases exposed by the module (works for both upstream and local builds).

    Returns True if the build succeeded, False otherwise.
    """
    module_dir = Path("/apps/Modules/modulefiles")
    needs_sudo = not os.access(module_dir, os.W_OK) if module_dir.exists() else True

    if needs_sudo:
        # Re-invoke with sudo, preserving the PATH so the shelley script is found.
        shelley_path = resolve_shelley_executable()
        if shelley_path is None:
            print_error("Could not locate the 'shelley' executable on PATH")
            return False

        cmd = [
            "sudo", "-E", "env", f"PATH={os.environ['PATH']}",
            shelley_path, "build", tool_spec,
        ]
        if edit_aliases:
            cmd.append("--edit-aliases")

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

    builder = CVMFSModuleBuilder()

    try:
        if "/" in tool_spec:
            tool_name, requested_version = tool_spec.split("/", 1)
        elif ":" in tool_spec:
            tool_name, requested_version = tool_spec.split(":", 1)
        else:
            tool_name, requested_version = tool_spec, None

        final_tool, final_version = builder.search_tool_version(tool_name, requested_version)

        with ShelleyStyle.create_status(f"Building module for {tool_spec}") as status:
            module_file = builder.shpc_install(
                final_tool, final_version, edit_aliases=edit_aliases, status=status,
            )
            available_versions = builder.list_versions(tool_name)

        if requested_version is None and len(available_versions) > 1:
            console.print(ShelleyStyle.create_build_info(final_tool, final_version, available_versions))
            print_rule()

        console.print(ShelleyStyle.create_build_success(final_tool, final_version, module_file))
        return True

    except Exception as e:
        title = "Build Failed"
        msg = str(e)
        suggestion = "Check that CVMFS is mounted and the tool exists"

        if re.search(r"^Version .* not found for", msg):
            suggestion = ""

        console.print(ShelleyStyle.create_error_panel(title=title, message=msg, suggestion=suggestion))
        return False


def list_cvmfs_versions(tool_name: str) -> None:
    """List available versions of a tool by scanning CVMFS directly."""
    builder = CVMFSModuleBuilder()

    try:
        with ShelleyStyle.create_status(f"Scanning CVMFS for {tool_name} versions") as status:
            version_path_pairs = builder.list_versions_with_paths(tool_name)

        if not version_path_pairs:
            console.print(ShelleyStyle.create_error_panel(
                "No Versions Found",
                f"No versions of '{tool_name}' found in CVMFS",
                "Check the tool name spelling or try a different tool",
            ))
        else:
            console.print(ShelleyStyle.create_versions_with_paths_table(tool_name, version_path_pairs))

    except Exception as e:
        console.print(ShelleyStyle.create_error_panel(
            "CVMFS Access Error",
            str(e),
            "Ensure CVMFS is mounted at /cvmfs/singularity.galaxyproject.org/",
        ))
