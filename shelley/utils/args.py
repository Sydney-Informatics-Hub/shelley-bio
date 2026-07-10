"""Argument-parsing helpers shared by the CLI and interactive dispatchers."""

import re


def parse_verbosity(args: list[str]) -> tuple[int, list[str]]:
    """Split verbosity flags from positional args.

    Counts each ``-v``/``--verbose`` as one level and ``-vv`` (etc.) by its
    number of ``v``s, so ``-v -v`` and ``-vv`` both yield level 2. Returns
    ``(verbosity, positionals)``.
    """
    verbosity = 0
    positional: list[str] = []
    for arg in args:
        if arg == "--verbose":
            verbosity += 1
        elif re.fullmatch(r"-v+", arg):
            verbosity += len(arg) - 1
        else:
            positional.append(arg)
    return verbosity, positional


def parse_build_flags(args: list[str]) -> tuple[bool, list[str]]:
    """Split ``build`` flags from positional args.

    Recognises ``--interactive``/``-i``, which opens an interactive session to
    curate the aliases the module exposes — deselect, rename, and add — for both
    upstream and local builds. Returns ``(interactive, positionals)``.
    """
    interactive = False
    positional: list[str] = []
    for arg in args:
        if arg in ("--interactive", "-i"):
            interactive = True
        else:
            positional.append(arg)
    return interactive, positional
