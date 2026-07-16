# References

## Parser

The main parser class is `plugin_img.parser.image_parser.DataRootParser`.

It exports the following behavior:

- `parse(mainfile, archive, logger)` — parse a sample folder and write `archive.data`
- `_find_synthesis_json(data_root)` — locate sample-level JSON metadata
- `_parse_image_folder(image_folder, data_root, log)` — parse one image experiment folder
- `_convert_npy_to_png(npy_path, log)` — generate a preview image from a raw NPY array

## Schema package

The plugin registers separate parser and schema entry points for each data type:

- `plugin_img.parser:image_parser_entry_point`
- `plugin_img.parser:hyperspectral_parser_entry_point`
- `plugin_img.plugin:image_schema_package_entry_point`
- `plugin_img.plugin:hyperspectral_schema_package_entry_point`

The schema package is defined in `plugin_img.plugin.image_plugin.m_package` and contains image analysis sections for:

- `ImageDataset`
- `ImageExperimentRun`
- `ImageMetadata`
- `ImageData`
- `ImageDimensions`
- `RegionOfInterest`
- `BoundingBox`
- `ImageVisualization`

## Sample data layout

Supported files and folders include:

- `synthesis.json` — sample-level synthesis or experiment conditions
- `metadata.json` — per-experiment image metadata
- `image_raw.npy` — raw image array data
- `image_preview.png` — preview image for visualization
- `manifest.csv` — legacy experiment manifest data


