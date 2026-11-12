# References

## Parser and editable ELN entries

The image, hyperspectral, and sulfurization parser entry points use NOMAD's
`ElnParserEntryPoint`. Each matching raw-file entry links to a user-editable ELN
entry. The ELN reads its source files on the first processing pass, preserves
manual edits on ordinary saves, and provides a **Reload from source** action to
replace source-derived values and regenerate plots.

## Schema packages

The plugin registers separate parser and schema entry points for each data type:

- `image_parser` and `image_schema`
- `hyperspectral_parser` and `hyperspectral_schema`
- `sulfurization_parser` and `sulfurization_schema`

Image schema sections include `ImageDataset`, `ImageExperimentRun`,
`ImageMetadata`, `ImageData`, `ImageDimensions`, `RegionOfInterest`,
`BoundingBox`, and `ImageVisualization`.

## Image sample data layout

Supported files and folders include:

- `synthesis.json` for sample-level synthesis or experiment conditions
- `metadata.json` for per-experiment image metadata
- `image_raw.npy` for raw image array data
- `image_preview.png` for an image preview
- `manifest.csv` for legacy experiment manifest data

## Hyperspectral source files

The hyperspectral parser matches an ENVI `.hdr` file and reads its associated
BIL data file. The linked ELN entry stores acquisition and cube metadata,
references to source and generated files, and analysis plots.
