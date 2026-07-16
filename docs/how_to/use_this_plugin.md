# How to Use This Plugin

The `plugin-img` parser reads image dataset folders and generates NOMAD entry data from image metadata and preview files.

## Supported folder layout

Example folder structure:

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

Supported file names include:

- `metadata.json`
- `image_raw.npy`
- `image_preview.png`
- `manifest.csv`
- `synthesis.json`

The parser creates one `ImageDataset` entry and one `ImageExperimentRun` per valid image folder.

## How to run the parser

Use NOMAD's parser invocation from your development environment or the `nomad` CLI that loads plugins.
In the plugin package, the parser class is `plugin_img.parser.image_parser.DataRootParser`.

## Fallback behavior

If a sample folder contains no image data but does contain sample metadata such as `synthesis.json`, the plugin still creates a NOMAD entry with the experimental details.

This ensures that the sample is not dropped entirely during parsing.

