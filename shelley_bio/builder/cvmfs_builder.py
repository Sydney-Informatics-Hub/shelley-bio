#!/usr/bin/env python3
"""
CVMFS Module Builder

Builds Lmod module files for tools available in CVMFS.
"""

import hashlib
import subprocess
import yaml
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
            raise RuntimeError(f"CVMFS not available at {self.cvmfs_singularity}")

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

    def _compute_sha256(self, path: str) -> str:
        """Compute the SHA-256 digest of a file (e.g. a SIF container)."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _is_registry_miss(self, output: str) -> bool:
        """Return True if shpc output indicates the tag is absent from the registry."""
        lower = output.lower()
        return any(p in lower for p in [
            "not found", "not in registry", "does not exist",
            "is not a known identifier", "no container", "unknown tag",
        ])

    def _run_shpc_install(self, uri_tag: str, container_path: str) -> Tuple[int, str]:
        """
        Run: shpc install <uri_tag> <container_path> --keep-path

        Returns (returncode, combined stdout+stderr).
        """
        result = subprocess.run(
            ["shpc", "install", uri_tag, container_path, "--keep-path"],
            capture_output=True, text=True,
        )
        return result.returncode, result.stdout + result.stderr

    def _ensure_local_registry_entry(
        self, tool_name: str, version: str, container_path: str, uri: str,
        local_registry: str = "/apps/local",
    ) -> None:
        """
        Create or update a local shpc registry entry for a CVMFS-only tag.

        Fetches the upstream container.yaml for the URI if available, then
        appends the missing tag+SHA256.  If the tool is entirely absent from
        the upstream registry a minimal container.yaml is created instead.
        """
        registry_dir = Path(local_registry) / uri
        registry_yaml = registry_dir / "container.yaml"
        registry_dir.mkdir(parents=True, exist_ok=True)

        # Try to pull the existing upstream entry
        remote_url = (
            f"https://raw.githubusercontent.com/singularityhub/shpc-registry/main/{uri}/container.yaml"
        )
        fetch = subprocess.run(
            ["curl", "-fsSL", remote_url, "-o", str(registry_yaml)],
            capture_output=True, text=True,
        )

        if fetch.returncode != 0 or not registry_yaml.exists():
            # Tool not in upstream registry — create a minimal config
            config: dict = {"docker": uri, "tags": {}, "filter": [version], "aliases": []}
        else:
            with open(registry_yaml) as f:
                config = yaml.safe_load(f) or {}

        # Append the missing tag
        if version not in config.get("tags", {}):
            sha256 = self._compute_sha256(container_path)
            config.setdefault("tags", {})[version] = f"sha256:{sha256}"
            with open(registry_yaml, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def shpc_install(self, tool_name: str, version: str) -> Path:
        """
        Install a CVMFS container as a functional Lmod module using shpc.

        shpc generates both the .lua module file and real wrapper scripts that
        put tool binaries on $PATH after `module load`.

        Steps:
          1. shpc install <uri>:<tag> <cvmfs-path> --keep-path
          2. If the tag is absent from the registry, create a local registry
             entry (fetching upstream container.yaml + computed SHA-256) and retry.
          3. Symlink <lmod_modules>/<tool>/<version>.lua -> shpc module.lua so
             `module load <tool>/<version>` works.

        shpc view install is not used — it re-pulls from Docker rather than
        reusing the --keep-path CVMFS install.

        Returns:
            Path to the symlinked .lua file (the user-facing module path).
        """
        uri = f"quay.io/biocontainers/{tool_name}"
        uri_tag = f"{uri}:{version}"
        container_path = str(self.cvmfs_singularity_path / f"{tool_name}:{version}")

        returncode, output = self._run_shpc_install(uri_tag, container_path)

        if returncode != 0:
            if self._is_registry_miss(output):
                self._ensure_local_registry_entry(tool_name, version, container_path, uri)
                returncode, output = self._run_shpc_install(uri_tag, container_path)

            if returncode != 0:
                raise RuntimeError(
                    f"shpc install failed for {uri_tag}:\n{output.strip()}"
                )

        shpc_module_base = Path(subprocess.run(
            ["shpc", "config", "get", "module_base"],
            capture_output=True, text=True, check=True,
        ).stdout.strip())
        src = shpc_module_base / "quay.io" / "biocontainers" / tool_name / version / "module.lua"
        dest_dir = self.lmod_modules_path / tool_name
        dest = dest_dir / f"{version}.lua"
        dest_dir.mkdir(parents=True, exist_ok=True)
        if dest.is_symlink() or dest.exists():
            dest.unlink()
        dest.symlink_to(src)

        return dest

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
            These are the exact inputs required for self.shpc_install.

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