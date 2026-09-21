"""Messages must take script labels from scripts.yml (via ``tool_ref``), not hardcode them."""

import os

import pytest

import cea
import cea.scripts

CEA_ROOT = os.path.dirname(cea.__file__)


def test_tool_ref_uses_registry_label():
    script = cea.scripts.by_name("final-energy")
    assert cea.scripts.tool_ref("final-energy") == f"'{script.label}' (cea final-energy)"


def test_tool_ref_unknown_script_raises():
    with pytest.raises(cea.ScriptNotFoundException):
        cea.scripts.tool_ref("no-such-script")


def test_no_hardcoded_tool_references():
    """A literal ``'<label>' (cea <name>)`` in a message goes stale as soon as a label is renamed."""
    references = [f"'{s.label}' (cea {s.name})" for s in cea.scripts.list_scripts(plugins=[])]
    offenders = []
    for folder, dirs, files in os.walk(CEA_ROOT):
        dirs[:] = [d for d in dirs if d != "tests"]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(folder, name)
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            offenders += [f"{os.path.relpath(path, CEA_ROOT)}: {ref}" for ref in references if ref in text]
    assert not offenders, "Use cea.scripts.tool_ref(script_name) instead of:\n" + "\n".join(offenders)
