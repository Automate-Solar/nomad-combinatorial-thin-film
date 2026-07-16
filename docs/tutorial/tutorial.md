# Tutorial

This tutorial walks through parsing a sample image dataset with the `plugin-img` parser and inspecting the resulting NOMAD entry structure.

## 1. Prepare a sample folder

Create a sample folder with the following files:

```text
sample-root/
    nomad_collect.txt
    synthesis.json
    20260323_133255/
        metadata.json
        image_raw.npy
        image_preview.png
        manifest.csv
```

The parser supports both `image_raw.npy` and `image_preview.png`, as well as optional manifest and synthesis JSON files.

## 2. Run the parser

Run the parser from the `packages/plugin-img` package root. If you use the `nomad` CLI or a local NOMAD development environment, make sure the plugin is installed in the same Python environment.

## 3. Verify the output

A successful parse creates an entry with the following structure:

- `ImageDataset`
- `measurements` list
    - `ImageExperimentRun`
        - `metadata`
        - `image`
        - `manifest_data`
        - `visualization`

If no image folder is present, the parser still creates an entry using `synthesis.json` and other experimental details.
