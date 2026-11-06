"""Invoke the ResumeBuilder Python engine CLI with dev/production mode switching.

Skills import this shared helper instead of calling ``uvx`` directly. The
``RESUMEBUILDER_TOOLS_MODE`` environment variable selects the target:

* ``dev``          -> run unpackaged local code via ``uv run -m python_engine.resume_tools``
* anything else    -> run the latest published package via ``uvx``

Default mode is ``production`` (``uvx``), so skills always resolve to the
latest tag on PyPI unless a developer explicitly opts into local development mode.
"""

from __future__ import annotations

import os
import subprocess
import sys

DEFAULT_MODE = "production"
DEV_MODE = "dev"
TOOL_VERSION = "latest"


def resolve_command(*args: str) -> list[str]:
    """Return the command list to invoke the engine CLI.

    ``RESUMEBUILDER_TOOLS_MODE=dev``  -> local unpackaged code via ``uv run``
    anything else / unset              -> published package via ``uvx``
    """
    mode = os.environ.get("RESUMEBUILDER_TOOLS_MODE", DEFAULT_MODE)
    if mode == DEV_MODE:
        return [sys.executable, "-m", "python_engine.resume_tools", *args]
    return ["uvx", f"resumebuilder-tools@{TOOL_VERSION}", *args]


def run(*args: str) -> None:
    """Invoke the engine CLI, honoring ``RESUMEBUILDER_TOOLS_MODE``.

    Raises :exc:`subprocess.CalledProcessError` if the command fails.
    """
    subprocess.run(resolve_command(*args), check=True)
