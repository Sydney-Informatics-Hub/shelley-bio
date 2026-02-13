#!/usr/bin/env python3
"""
CVMFS Module Builder

Builds Lmod module files for tools available in CVMFS.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import re

from ..utils.style import console, ShelleyStyle


class CVMFSModuleBuilder:
    """Builds Lmod modules for CVMFS tools."""
    
    CVMFS_SINGULARITY_PATH = Path("/cvmfs/singularity.galaxyproject.org/all")
    LMOD_MODULES_PATH = Path("/apps/Modules/modulefiles")
    
    def __init__(self):
        """Initialize the module builder."""
        pass
    
    def _is_cvmfs_available(self) -> bool:
        """Check if CVMFS is mounted and accessible."""
        return self.CVMFS_SINGULARITY_PATH.exists() and self.CVMFS_SINGULARITY_PATH.is_dir()
    
    def _get_available_tools(self, tool_name: str) -> List[Tuple[str, str]]:
        """
        Get available versions of a tool from CVMFS.
        
        Args:
            tool_name: Name of the tool to search for
            
        Returns:
            List of (tool_name, version) tuples
        """
        if not self._is_cvmfs_available():
            raise RuntimeError("CVMFS not available at /cvmfs/singularity.galaxyproject.org/all")
        
        # Search for containers matching the tool name
        try:
            containers = []
            for item in self.CVMFS_SINGULARITY_PATH.iterdir():
                if item.is_file() or item.is_symlink():
                    # Container names are like "samtools:1.22" 
                    name = item.name
                    if ":" in name:
                        container_tool, version = name.split(":", 1)
                        if container_tool.lower() == tool_name.lower():
                            containers.append((container_tool, version))
            
            return containers
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Failed to read CVMFS directory: {e}")
    
    def _parse_version(self, version_str: str) -> Tuple[int, ...]:
        """
        Parse version string for semantic sorting.
        
        Args:
            version_str: Version string like "1.21" or "1.22--hdfd78af_0"
            
        Returns:
            Tuple of version numbers for sorting
        """
        # Extract the main version number before any build suffix
        version_part = version_str.split("--")[0]
        
        # Split on dots and convert to integers where possible
        parts = []
        for part in version_part.split("."):
            # Try to extract numbers from the part
            numbers = re.findall(r'\d+', part)
            if numbers:
                parts.extend(int(num) for num in numbers)
            else:
                # For non-numeric parts, use ASCII value of first char
                parts.append(ord(part[0]) if part else 0)
        
        return tuple(parts)
    
    def _get_latest_version(self, versions: List[Tuple[str, str]]) -> Tuple[str, str]:
        """
        Get the latest version from a list of versions.
        
        Args:
            versions: List of (tool_name, version) tuples
            
        Returns:
            The (tool_name, version) tuple with the latest version
        """
        if not versions:
            raise ValueError("No versions provided")
        
        # Sort by version, latest first
        sorted_versions = sorted(versions, key=lambda x: self._parse_version(x[1]), reverse=True)
        return sorted_versions[0]
    
    def _create_module_file(self, tool_name: str, version: str) -> Path:
        """
        Create an Lmod module file for the specified tool and version.
        
        Args:
            tool_name: Name of the tool
            version: Version of the tool
            
        Returns:
            Path to the created module file
            
        Raises:
            PermissionError: If unable to write to module directory
        """
        # Create module directory
        module_dir = self.LMOD_MODULES_PATH / tool_name
        module_file = module_dir / f"{version}.lua"
        
        try:
            module_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionError(
                f"Permission denied creating module directory: {module_dir}\n"
                f"You must run this command with sudo privileges."
            )
        
        # Container path
        container_path = f"/cvmfs/singularity.galaxyproject.org/all/{tool_name}:{version}"
        
        # Module content
        module_content = f'''help([[{tool_name.title()} {version} from CVMFS

This module provides access to {tool_name} version {version} via Singularity container.
All executables from the container are available in your PATH.

Usage examples:
  For BLAST: blastn, blastp, blastx, tblastn, tblastx
  For other tools: see container documentation

Container path: {container_path}
]])

load("singularity")

local containerPath = "{container_path}"

-- Function to execute commands in container
local function container_exec(cmd)
    return "singularity exec " .. containerPath .. " " .. cmd
end

-- Add container executables to PATH via wrapper functions
prepend_path("PATH", pathJoin(os.getenv("MODULEPATH") or "", "..", "wrappers", "{tool_name}", "{version}"))

-- Create primary alias for the tool name (if executable exists)
set_alias("{tool_name}", container_exec("{tool_name}"))

-- For tools with known multiple executables, create additional aliases
if "{tool_name}" == "blast" then
    set_alias("blastn", container_exec("blastn"))
    set_alias("blastp", container_exec("blastp"))
    set_alias("blastx", container_exec("blastx"))
    set_alias("tblastn", container_exec("tblastn"))
    set_alias("tblastx", container_exec("tblastx"))
    set_alias("makeblastdb", container_exec("makeblastdb"))
    set_alias("blast_formatter", container_exec("blast_formatter"))
end

if "{tool_name}" == "samtools" then
    set_alias("samtools", container_exec("samtools"))
end

if "{tool_name}" == "fastqc" then
    set_alias("fastqc", container_exec("fastqc"))
end

-- Generic function to run any command in the container
set_alias("{tool_name}_exec", container_exec("$*"))
'''
        
        try:
            module_file.write_text(module_content)
        except PermissionError:
            raise PermissionError(
                f"Permission denied writing module file: {module_file}\n"
                f"You must run this command with sudo privileges."
            )
        
        return module_file
    
    def _refresh_module_cache(self) -> Tuple[bool, str]:
        """
        Refresh the Lmod module cache.
        
        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                ["module", "--ignore_cache", "avail"],
                capture_output=True,
                text=True,
                check=False
            )
            return True, result.stderr  # module avail outputs to stderr
        except FileNotFoundError:
            return False, "Lmod not available (module command not found)"
        except Exception as e:
            return False, f"Error running module command: {e}"
    
    def list_versions(self, tool_name: str) -> List[str]:
        """
        List available versions of a tool without creating a module.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            List of version strings
        """
        versions = self._get_available_tools(tool_name)
        if not versions:
            return []
        
        # Sort versions newest first
        sorted_versions = sorted(versions, key=lambda x: self._parse_version(x[1]), reverse=True)
        return [version for _, version in sorted_versions]
    
    def list_versions_with_paths(self, tool_name: str) -> List[Tuple[str, str]]:
        """
        List available versions of a tool with their full CVMFS paths.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            List of (version, full_path) tuples
        """
        versions = self._get_available_tools(tool_name)
        if not versions:
            return []
        
        # Sort versions newest first and create full paths
        sorted_versions = sorted(versions, key=lambda x: self._parse_version(x[1]), reverse=True)
        return [(version, str(self.CVMFS_SINGULARITY_PATH / f"{tool_name}:{version}")) 
                for _, version in sorted_versions]
    
    def build_module(self, tool_spec: str, force_version: Optional[str] = None) -> Tuple[str, str, Path]:
        """
        Build an Lmod module for a tool.
        
        Args:
            tool_spec: Tool specification like "samtools" or "samtools/1.21"
            force_version: Force a specific version (overrides tool_spec version)
            
        Returns:
            Tuple of (tool_name, version, module_file_path)
            
        Raises:
            ValueError: If tool not found or version not available
            RuntimeError: If CVMFS not available
            PermissionError: If unable to create module files
        """
        # Parse tool specification
        if "/" in tool_spec and force_version is None:
            tool_name, requested_version = tool_spec.split("/", 1)
        else:
            tool_name = tool_spec
            requested_version = force_version
        
        # Get available versions
        available_versions = self._get_available_tools(tool_name)
        
        if not available_versions:
            raise ValueError(f"Tool '{tool_name}' not found in CVMFS")
        
        # Determine version to use
        if requested_version:
            # Check if requested version exists
            matching_versions = [
                (t, v) for t, v in available_versions 
                if v == requested_version
            ]
            if not matching_versions:
                available_list = [v for _, v in available_versions]
                raise ValueError(
                    f"Version '{requested_version}' not found for '{tool_name}'. "
                    f"Available versions: {', '.join(sorted(available_list))}"
                )
            final_tool, final_version = matching_versions[0]
        else:
            # Use latest version
            final_tool, final_version = self._get_latest_version(available_versions)
        
        # Create module file
        module_file = self._create_module_file(final_tool, final_version)
        
        return final_tool, final_version, module_file


def format_versions_list(versions: List[str]) -> None:
    """Display a formatted list of versions using Rich."""
    if not versions:
        console.print(ShelleyStyle.create_info_panel("No Versions", "No versions found for this tool"))
        return
    
    # Create a nice table of versions
    from rich.table import Table
    
    table = Table(
        title="[header]Available Versions[/header]",
        show_header=True,
        header_style="table.header",
        border_style="border"
    )
    
    table.add_column("Version", style="version")
    table.add_column("Status", style="success")
    
    for version in versions:
        table.add_row(version, "✓ Available")
    
    console.print(table)


def format_build_output(
    tool_name: str, 
    version: str, 
    module_file: Path, 
    available_versions: List[str], 
    requested_version: Optional[str] = None
) -> None:
    """Display formatted build output using Rich."""
    # This function is now handled by the ShelleyStyle class methods
    # in the CLI client, so we just pass through
    pass