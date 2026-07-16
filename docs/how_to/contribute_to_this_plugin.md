# Contribute to This Plugin

Contributions should improve parser coverage, add support for new image formats, or improve documentation.

## Recommended workflow

1. Fork the repository and create a feature branch.
2. Add or update tests in `packages/plugin-img/tests`.
3. Run the plugin test suite:

```powershell
Set-Location .\packages\plugin-img
python -m pytest -sv tests
```

4. Run the documentation locally if you changed docs:

```powershell
mkdocs serve
```

5. Commit your changes and open a pull request.

## What to document

- new parser behavior
- supported folder layouts
- sample data assumptions
- any new schema or metadata fields

