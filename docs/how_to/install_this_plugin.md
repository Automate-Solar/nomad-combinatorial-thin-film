# Install This Plugin

This document describes how to install `plugin-img` for local development and how to register it in a local NOMAD setup.

## Local development installation

From the `packages/plugin-img` directory:

```powershell
Set-Location .\packages\plugin-img
uv pip install -e '.[dev]'
```

This installs the plugin in editable mode with development dependencies.

## Running the package tests

Run the plugin test suite from the package root:

```powershell
python -m pytest -sv tests
```

## Building documentation locally

Use MkDocs to preview the documentation:

```powershell
mkdocs serve
```

Then open the local browser URL shown in the terminal.

## Notes for NOMAD integration

In a local NOMAD development environment, make sure that the plugin package is installed into the same Python environment used by NOMAD. For the shared `nomad-distro-dev-param` workspace, install the plugin from the workspace root if needed.
