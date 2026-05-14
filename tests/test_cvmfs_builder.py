#!/usr/bin/env python3
"""pytest coverage for CVMFSModuleBuilder: version resolution and shpc-based installation."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shelley_bio.builder.cvmfs_builder import CVMFSModuleBuilder
from shelley_bio.client.cli import build_module

# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

FAKE_VERSIONS = [
    ("samtools", "1.23.1--ha83d96e_0"),  # latest
    ("samtools", "1.21--h96c455f_1"),
    ("samtools", "1.21--h50ea8bc_0"),
]


@pytest.fixture
def builder(tmp_path) -> CVMFSModuleBuilder:
    return CVMFSModuleBuilder(lmod_modules=str(tmp_path / "modulefiles"))


def _make_subprocess_run(shpc_base: Path, install_rc: int = 0,
                         install_out: str = "Module was created.\n"):
    """Return a subprocess.run side-effect that handles shpc install and config calls."""
    def fake_run(cmd, **_):
        m = MagicMock()
        m.stderr = ""
        if "module_base" in cmd:
            m.returncode = 0
            m.stdout = str(shpc_base)
        else:
            m.returncode = install_rc
            m.stdout = install_out
        return m
    return fake_run


# ---------------------------------------------------------------------------
# Existing version-resolution tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "tool_name,tool_version",
    [('samtools', '1.21'), ('plink2', '2.00a5.12')]
)
def test_search_tool_version_multiplebuilds(builder, tool_name, tool_version):
    # Both of these versions have multiple builds; interactive selection should be triggered.
    # Mock questionary so the test runs headlessly.
    with patch("shelley_bio.builder.cvmfs_builder.questionary") as mock_q:
        available = builder._get_available_tools(tool_name)
        matches = [
            (t, v) for t, v in available
            if v == tool_version or v.split("--", 1)[0] == tool_version
        ]
        assert len(matches) > 1, "Precondition: test requires multiple builds"
        first_match = matches[0]
        mock_q.select.return_value.ask.return_value = first_match

        result = builder.search_tool_version(tool_name, tool_version)

        mock_q.select.assert_called_once()
        assert result[0] == tool_name
        assert result[1].split("--", 1)[0] == tool_version

@pytest.mark.parametrize(
    "tool_name,tool_version", 
    [('samtools', '1.21--h96c455f_1'), ('plink2', '2.00a5.12--h4ac6f70_0')]
) 
def test_search_tool_version_singlebuild(builder, tool_name, tool_version):
    # Both of these versions have only a single build
    exp = (tool_name, tool_version)
    get = builder.search_tool_version(tool_name, tool_version)
    assert get == exp

@pytest.mark.parametrize(
    "tool_name,tool_version,latest_version",
    [('samtools', None, '1.23.1--ha83d96e_0'), ('plink2', None, '2.00a5.12--h4ac6f70_0')]
)
def test_search_tool_version_none(builder, tool_name, tool_version, latest_version):
    # When no version is provided, build the latest version
    exp = (tool_name, latest_version)
    get = builder.search_tool_version(tool_name, tool_version)
    assert get == exp


# ---------------------------------------------------------------------------
# shpc_install unit tests
# ---------------------------------------------------------------------------

def test_shpc_install_success(builder, tmp_path):
    """Happy path: shpc install succeeds and symlink is created at the right path."""
    tool, version = "samtools", "1.21--h96c455f_1"
    shpc_base = tmp_path / "shpc_modules"
    src = shpc_base / "quay.io" / "biocontainers" / tool / version / "module.lua"
    src.parent.mkdir(parents=True)
    src.touch()

    with patch("shelley_bio.builder.cvmfs_builder.subprocess.run",
               side_effect=_make_subprocess_run(shpc_base)):
        dest = builder.shpc_install(tool, version)

    assert dest == builder.lmod_modules_path / tool / f"{version}.lua"
    assert dest.is_symlink()
    assert dest.resolve() == src.resolve()


def test_shpc_install_registry_miss_retries(builder, tmp_path):
    """Registry miss on first attempt triggers local entry creation then a retry."""
    tool, version = "samtools", "1.21--h96c455f_1"
    shpc_base = tmp_path / "shpc_modules"
    src = shpc_base / "quay.io" / "biocontainers" / tool / version / "module.lua"
    src.parent.mkdir(parents=True)
    src.touch()

    install_calls = {"n": 0}

    def fake_run(cmd, **_):
        m = MagicMock()
        m.stderr = ""
        if "module_base" in cmd:
            m.returncode = 0
            m.stdout = str(shpc_base)
        else:
            install_calls["n"] += 1
            if install_calls["n"] == 1:
                m.returncode = 1
                m.stdout = "quay.io/biocontainers/samtools:1.21--h96c455f_1 is not a known identifier."
            else:
                m.returncode = 0
                m.stdout = "Module was created.\n"
        return m

    with patch("shelley_bio.builder.cvmfs_builder.subprocess.run", side_effect=fake_run), \
         patch.object(builder, "_ensure_local_registry_entry") as mock_ensure:
        dest = builder.shpc_install(tool, version)

    mock_ensure.assert_called_once()
    assert install_calls["n"] == 2
    assert dest.is_symlink()


def test_shpc_install_hard_failure_raises(builder, tmp_path):
    """Non-registry shpc failure raises RuntimeError containing the shpc output."""
    shpc_base = tmp_path / "shpc_modules"

    with patch("shelley_bio.builder.cvmfs_builder.subprocess.run",
               side_effect=_make_subprocess_run(shpc_base, install_rc=1,
                                                install_out="Unexpected shpc error")):
        with pytest.raises(RuntimeError, match="shpc install failed"):
            builder.shpc_install("samtools", "1.21--h96c455f_1")


# ---------------------------------------------------------------------------
# build_module input format tests
# ---------------------------------------------------------------------------
# These test that build_module correctly parses the tool spec and routes to
# shpc_install with the right arguments.  CVMFSModuleBuilder is patched at the
# class level so spec-parsing inside build_module is still exercised.

@pytest.fixture
def mock_builder_cls(tmp_path):
    """Patch CVMFSModuleBuilder inside cli with a mock instance."""
    fake_builder = MagicMock(spec=CVMFSModuleBuilder)
    fake_builder.search_tool_version.side_effect = lambda tool, ver=None: (
        tool,
        {
            None: "1.23.1--ha83d96e_0",
            "1.21": "1.21--h96c455f_1",
            "1.21--h96c455f_1": "1.21--h96c455f_1",
        }[ver]
    )
    fake_builder.shpc_install.return_value = tmp_path / "samtools" / "dummy.lua"
    fake_builder.list_versions.return_value = [v for _, v in FAKE_VERSIONS]

    with patch("shelley_bio.client.cli.CVMFSModuleBuilder", return_value=fake_builder), \
         patch("os.access", return_value=True), \
         patch("shelley_bio.client.cli.ShelleyStyle.create_status") as mock_status, \
         patch("shelley_bio.client.cli.console"):
        mock_status.return_value.__enter__ = MagicMock(return_value=None)
        mock_status.return_value.__exit__ = MagicMock(return_value=False)
        yield fake_builder


def test_build_no_version(mock_builder_cls):
    """build_module('samtools') installs the latest tag."""
    result = build_module("samtools")

    assert result is True
    mock_builder_cls.shpc_install.assert_called_once_with("samtools", "1.23.1--ha83d96e_0")


def test_build_short_version(mock_builder_cls):
    """build_module('samtools/1.21') installs the full tag after version resolution."""
    result = build_module("samtools/1.21")

    assert result is True
    mock_builder_cls.shpc_install.assert_called_once_with("samtools", "1.21--h96c455f_1")


def test_build_full_tag(mock_builder_cls):
    """build_module('samtools/1.21--h96c455f_1') installs the exact tag without prompting."""
    result = build_module("samtools/1.21--h96c455f_1")

    assert result is True
    mock_builder_cls.shpc_install.assert_called_once_with("samtools", "1.21--h96c455f_1")


# ---------------------------------------------------------------------------
# _ensure_local_registry_entry alias generation
# ---------------------------------------------------------------------------

def test_ensure_local_registry_populates_aliases_on_miss(builder, tmp_path):
    """When upstream registry returns 404, aliases are populated via guts diff."""
    fake_aliases = [{"name": "bwa", "command": "bwa"}]
    with patch("shelley_bio.builder.cvmfs_builder.subprocess.run") as mock_run, \
         patch("shelley_bio.builder.cvmfs_builder.extract_aliases", return_value=fake_aliases), \
         patch.object(builder, "_compute_sha256", return_value="abc123"):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")
        builder._ensure_local_registry_entry(
            "bwa", "0.7.17--hed695b0_7",
            "/cvmfs/.../bwa:0.7.17--hed695b0_7",
            "quay.io/biocontainers/bwa",
            local_registry=str(tmp_path),
        )
    import yaml
    config = yaml.safe_load(
        (tmp_path / "quay.io/biocontainers/bwa/container.yaml").read_text()
    )
    assert config["aliases"] == fake_aliases


def test_ensure_local_registry_fills_empty_upstream_aliases(builder, tmp_path):
    """When upstream container.yaml has empty aliases, guts diff fills them in."""
    fake_aliases = [{"name": "samtools", "command": "samtools"}]
    registry_dir = tmp_path / "quay.io/biocontainers/samtools"
    registry_dir.mkdir(parents=True)
    (registry_dir / "container.yaml").write_text(
        "docker: quay.io/biocontainers/samtools\naliases: []\ntags: {}\n"
    )
    with patch("shelley_bio.builder.cvmfs_builder.subprocess.run") as mock_run, \
         patch("shelley_bio.builder.cvmfs_builder.extract_aliases", return_value=fake_aliases), \
         patch.object(builder, "_compute_sha256", return_value="abc123"):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        builder._ensure_local_registry_entry(
            "samtools", "1.21--h96c455f_1",
            "/cvmfs/.../samtools:1.21--h96c455f_1",
            "quay.io/biocontainers/samtools",
            local_registry=str(tmp_path),
        )
    import yaml
    config = yaml.safe_load((registry_dir / "container.yaml").read_text())
    assert config["aliases"] == fake_aliases


def test_extract_aliases_returns_empty_on_import_error():
    """extract_aliases degrades gracefully when container-guts is not installed."""
    from shelley_bio.builder.guts_integration import extract_aliases
    with patch.dict("sys.modules", {
        "container_guts": None,
        "container_guts.main": None,
        "container_guts.main.client": None,
        "container_guts.defaults": None,
    }):
        result = extract_aliases("/cvmfs/foo/bar:1.0")
    assert result == []
