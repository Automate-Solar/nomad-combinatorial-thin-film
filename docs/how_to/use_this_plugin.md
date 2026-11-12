# How to Use the Image and Hyperspectral Plugins

The image and hyperspectral parsers use NOMAD's hybrid ELN workflow. Uploading a
matching source file creates a raw-file entry and a linked editable ELN entry.
The ELN entry reads the source files on its first processing pass. Later saves
preserve manual edits and refresh the plots from the current entry values.

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

The image ELN entry contains one `ImageExperimentRun` per valid image folder.

## Editing and reloading data

Edit quantities in the linked ELN entry and save it to preserve those edits. Use
the **Reload from source** action to replace source-derived quantities from the
uploaded files and regenerate previews and plots. User notes are kept when reloading.

The hyperspectral parser matches an ENVI `.hdr` file and reads its associated BIL
file. Each linked ELN entry contains the metadata, cube references, RGB preview,
and analysis plots for that measurement.

## Fallback behavior

If a sample folder contains no image data but does contain sample metadata such as `synthesis.json`, the plugin still creates an editable ELN entry with the experimental details.

This ensures that the sample is not dropped entirely during parsing.

