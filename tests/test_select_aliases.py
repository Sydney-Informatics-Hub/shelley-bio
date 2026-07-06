"""Tests for the interactive alias selector used by `build --detect-bins`."""

from unittest.mock import MagicMock, patch

import pytest

from shelley.builder.guts_integration import select_aliases


def _fake_checkbox(return_value):
    """Build a questionary.checkbox stub returning ``return_value`` from .ask()."""
    stub = MagicMock()
    stub.checkbox.return_value.ask.return_value = return_value
    # Preserve Choice so select_aliases can build choices as usual.
    from shelley.builder.guts_integration import questionary as real_q
    stub.Choice = real_q.Choice
    return stub


def test_select_aliases_empty_returns_empty_without_prompt():
    with patch("shelley.builder.guts_integration.questionary") as mock_q:
        assert select_aliases([]) == []
        mock_q.checkbox.assert_not_called()


def test_select_aliases_returns_chosen_subset():
    aliases = [
        {"name": "vcftools", "command": "vcftools"},
        {"name": "telnet", "command": "telnet"},
    ]
    chosen = [aliases[0]]
    with patch("shelley.builder.guts_integration.questionary",
               _fake_checkbox(chosen)):
        assert select_aliases(aliases) == chosen


def test_select_aliases_cancel_raises():
    aliases = [{"name": "vcftools", "command": "vcftools"}]
    with patch("shelley.builder.guts_integration.questionary",
               _fake_checkbox(None)):
        with pytest.raises(ValueError):
            select_aliases(aliases)
