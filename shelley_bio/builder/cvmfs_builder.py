#!/usr/bin/env python3
"""
CVMFS Module Builder

Builds Lmod module files for tools available in CVMFS.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
import re
import questionary
from datetime import datetime

class CVMFSModuleBuilder:
    """Builds Lmod modules for CVMFS tools."""
    
    def __init__(
        self,
        cvmfs_singularity: str = "/cvmfs/singularity.galaxyproject.org/all", 
        lmod_modules: str = "/apps/Modules/modulefiles"
    ):
        self.cvmfs_singularity = cvmfs_singularity
        self.lmod_modules = lmod_modules
        self.cvmfs_singularity_path = Path(self.cvmfs_singularity)
        self.lmod_modules_path = Path(self.lmod_modules)

    def _is_cvmfs_available(self) -> bool:
        """Check if CVMFS is mounted and accessible."""
        return self.cvmfs_singularity_path.exists() and self.cvmfs_singularity_path.is_dir()
    
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
    
    def _sort_versions(self, versions: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Sort versions by semantic versioning, newest first."""
        return sorted(versions, key=lambda x: self._parse_version(x[1]), reverse=True)
    
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
            for item in self.cvmfs_singularity_path.iterdir():
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
        sorted_versions = self._sort_versions(versions)
        return sorted_versions[0]
    
    def create_module_file(self, tool_name: str, version: str) -> Path:
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
        module_dir = self.lmod_modules_path / tool_name
        module_file = module_dir / f"{version}.lua"
        
        try:
            module_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise PermissionError(
                f"Permission denied creating module directory: {module_dir}\n"
                f"You must run this command with sudo privileges."
            )
        
        # Container path
        container_path = f"{self.cvmfs_singularity_path}/{tool_name}:{version}"
        
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
        sorted_versions = self._sort_versions(versions)
        return [version for _, version in sorted_versions]

    def list_versions_with_paths(self, tool_name: str) -> List[Tuple[str, str]]:
        """
        List available versions of a tool with their full CVMFS paths.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            List of (version, full_path) tuples
        """
        sorted_versions = self.list_versions(tool_name)
        return [(version, str(self.cvmfs_singularity_path / f"{tool_name}:{version}"))
                for version in sorted_versions]

    def _select_version_interactively(
        self,
        tool_name: str,
        matches: List[Tuple[str, str]],
        labels: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """
        Prompt the user to pick one build when multiple exist for the same short version.

        Args:
            tool_name: Name of the tool (used only for display).
            matches: ``(tool, full_version)`` tuples, sorted newest-first.
            labels: Optional pre-built display strings (one per match).
                    Falls back to the raw version string when omitted.
        """
        if labels is None:
            labels = [ver for _, ver in matches]

        choices = [
            questionary.Choice(title=label, value=match)
            for label, match in zip(labels, matches)
        ]

        selected = questionary.select(
            f"Multiple builds found for {tool_name}. Select one to install:",
            choices=choices,
        ).ask()

        if selected is None:
            raise ValueError("Version selection cancelled.")

        return selected
    
    def search_tool_version(self, tool_name: str, requested_version: Optional[str] = None) -> Tuple[str, str]:
        """
        Searches for a tool name to the requested version or the latest version if not provided.
        Also handles the case of multiple matching versions.

        Args:
            tool_name: Name of the tool to search in CVMFS.
            requested_version: Optional full or short version string to match.

        Returns:
            A ``(tool_name, version)`` tuple for the selected tool version. 
            These are the exact inputs required for self.create_module_file.

        Raises:
            ValueError: If no matching version exists or the request is ambiguous.
        """
        # Get available versions as (tool, full_version) tuples
        available_versions = self._get_available_tools(tool_name)

        if requested_version is None:
            # If no version was specified, return the latest version
            final_tool, final_version = self._get_latest_version(available_versions)
            return final_tool, final_version

        # If a version was provided, match against both full versions ("1.21--h50ea8bc_3") and short ones ("1.21")
        matches = [
            (tool, ver)
            for tool, ver in available_versions
            if ver == requested_version or ver.split("--", 1)[0] == requested_version
        ]

        if not matches:
            short_versions = sorted({ver.split("--", 1)[0] for _, ver in available_versions})
            raise ValueError(
                f"Version '{requested_version}' not found for '{tool_name}'. "
                f"Available versions: {', '.join(short_versions)}"
            )
        
        if len(matches) > 1:
            def _mtime(ver: str) -> float:
                try:
                    return (self.cvmfs_singularity_path / f"{tool_name}:{ver}").stat().st_mtime
                except OSError:
                    return 0.0

            matches_sorted = sorted(matches, key=lambda x: _mtime(x[1]), reverse=True)

            labels = []
            for _, ver in matches_sorted:
                path = self.cvmfs_singularity_path / f"{tool_name}:{ver}"
                try:
                    stat = path.stat()
                    size_mb = stat.st_size / (1024 ** 2)
                    modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                    labels.append(f"{ver}  ({size_mb:.1f} MB, modified {modified})")
                except OSError:
                    labels.append(ver)

            return self._select_version_interactively(tool_name, matches_sorted, labels)
            
        return matches[0]