"""Package activation helpers for the plugin-img development layout.

This module provides a convenience function `activate_all()` which will
import the plugin subpackages found under this `src/` directory. During
development you can either add `packages/plugin-img/src` to your `PYTHONPATH`
or install the package editable with `pip install -e packages/plugin-img`.

Usage examples:

        # Add to PYTHONPATH (temporary for this shell):
        set PYTHONPATH=%PYTHONPATH%;C:\path\to\repo\packages\plugin-img\src
        python -c "import src; src.activate_all()"

        # Or, after `pip install -e packages/plugin-img`:
        python -c "import src; src.activate_all()"

The function tries to import the common subpackages used by this plugin
bundle so that any parser registration side-effects occur on import.
"""

from importlib import import_module

_DEFAULT_SUBPACKAGES = ['nomad_combinatorial_thin_film']


def activate_all(subpackages: list[str] | None = None) -> None:
    """Import subpackages to ensure their modules and potential parser
    registration side-effects run.

    - If `subpackages` is None, a default list is imported.
    - This is a convenience during development; prefer installing the
      package in editable mode for production use.
    """
    names = subpackages or _DEFAULT_SUBPACKAGES
    for name in names:
        try:
            import_module(name)
        except Exception:
            # Do not hard-fail here; the developer can inspect import
            # errors if activation doesn't work in their environment.
            pass


__all__ = ['activate_all']
