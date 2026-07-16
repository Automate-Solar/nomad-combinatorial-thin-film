---
title: plugin-img documentation
---

# plugin-img documentation

`plugin-img` is the NOMAD plugin for image analysis datasets. It converts image folders, acquisition metadata, and preview files into NOMAD entry data.

## Getting started

- [Install this plugin](how_to/install_this_plugin.md)
- [Use this plugin](how_to/use_this_plugin.md)
- [Run the tutorial](tutorial/tutorial.md)
- [Contribute to the plugin](how_to/contribute_to_this_plugin.md)
- [Contribute to documentation](how_to/contribute_to_the_documentation.md)

## What this plugin does

The plugin reads image sample folders and extracts:

- sample-level synthesis conditions from JSON files
- per-sample `metadata.json`
- image arrays from `image_raw.npy`
- preview images from `image_preview.png`
- legacy manifest data from `manifest.csv`

It creates a NOMAD entry even when a sample contains only synthesis metadata and no image files.

## Documentation overview

- [Tutorial](tutorial/tutorial.md) — parse a sample image dataset and inspect the output
- [How-to guides](how_to/install_this_plugin.md) — installation and local usage
- [Reference](reference/references.md) — parser and schema package reference
