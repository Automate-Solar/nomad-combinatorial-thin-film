import logging
from io import BytesIO
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import numpy as np
from nomad.parsing.parser import MatchingParser

from nomad_combinatorial_thin_film.parser.utils import (
    ENVI_DTYPE_MAP,
    HyperspectralAnalysis,
    HyperspectralMeasurement,
    HyperspectralRawData,
    build_acquisition_metadata,
    build_cube_metadata,
    collect_dataset_figures,
    create_rgb_preview_image,
    extract_wavelengths,
    find_hyperspectral_folders,
    parse_hyperspectral_folder,
    read_bil,
    read_envi_hdr,
)
from nomad_combinatorial_thin_film.plugin.hyperspectral_plugin import (
    HyperspectralDataset,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive

logger_module = logging.getLogger(__name__)


def _normalize_upload_path(path):
    """Convert a selected upload path into a path relative to NOMAD's raw root."""
    normalized = str(path).replace('\\', '/')
    marker = '/raw/'
    if marker in normalized:
        return normalized.split(marker, 1)[1]
    if normalized.startswith('raw/'):
        return normalized[4:]
    return normalized.lstrip('/')


def _find_bil_upload_path(context, hdr_path):
    """Find the BIL file paired with an uploaded ENVI header."""
    upload_files = context.upload_files
    header = PurePosixPath(hdr_path)

    if header.name.lower().endswith('.bil.hdr'):
        paired_path = hdr_path[:-4]
        if upload_files.raw_isfile(paired_path):
            return paired_path

    directory = '' if str(header.parent) == '.' else header.parent.as_posix()
    candidates = [
        item.path
        for item in upload_files.raw_listdir(directory, files_only=True)
        if item.path.lower().endswith('.bil')
    ]
    same_stem = f'{header.stem}.bil'.lower()
    for candidate in candidates:
        if PurePosixPath(candidate).name.lower() == same_stem:
            return candidate
    if len(candidates) == 1:
        return candidates[0]
    raise FileNotFoundError(
        f'Could not identify the BIL file for {hdr_path!r}; '
        f'found {candidates!r}.'
    )


def _register_generated_file(context, relative_path):
    """Register an ENVI-derived file in upload storage."""
    context.process_updated_raw_file(relative_path, allow_modify=True)


def _build_hyperspectral_dataset_from_context(hdr_path, context, log):
    """Read an ENVI measurement through NOMAD's raw-file API."""
    hdr_path = _normalize_upload_path(hdr_path)
    bil_path = _find_bil_upload_path(context, hdr_path)

    with context.raw_file(hdr_path, 'rt') as hdr_file:
        hdr = read_envi_hdr(hdr_file)
    wavelengths = extract_wavelengths(hdr)
    dtype = ENVI_DTYPE_MAP[str(hdr['data type'])]
    with context.raw_file(bil_path, 'rb') as bil_file:
        cube = read_bil(
            bil_file,
            lines=int(hdr['lines']),
            samples=int(hdr['samples']),
            bands=int(hdr['bands']),
            dtype=dtype,
        )

    parent = PurePosixPath(hdr_path).parent
    prefix = '' if str(parent) == '.' else f'{parent.as_posix()}/'
    output_stem = PurePosixPath(hdr_path).name.removesuffix('.hdr')
    cube_path = f'{prefix}{output_stem}_cube.npy'
    preview_path = f'{prefix}{output_stem}_rgb_preview.png'
    with context.raw_file(cube_path, 'wb') as cube_file:
        np.save(cube_file, cube.astype(np.float32))
    _register_generated_file(context, cube_path)

    preview = create_rgb_preview_image(cube, wavelengths, log)
    if preview is not None:
        preview_bytes = BytesIO()
        preview.save(preview_bytes, format='PNG')
        with context.raw_file(preview_path, 'wb') as preview_file:
            preview_file.write(preview_bytes.getvalue())
        _register_generated_file(context, preview_path)
    else:
        preview_path = None

    measurement = HyperspectralMeasurement()
    measurement.acquisition_metadata = build_acquisition_metadata(hdr)
    measurement.cube_metadata = build_cube_metadata(hdr, wavelengths)
    measurement.raw_data = HyperspectralRawData(
        hdr_file=hdr_path,
        bil_file=bil_path,
        cube_npy=cube_path,
        rgb_preview=preview_path,
    )
    measurement.visualization = HyperspectralAnalysis()

    from nomad_combinatorial_thin_film.plugin.utils import (
        create_hyperspectral_overview_figures,
    )

    measurement.visualization.figures = create_hyperspectral_overview_figures(
        cube,
        wavelengths,
        log,
    )
    measurement.label = PurePosixPath(hdr_path).parent.name or PurePosixPath(
        hdr_path
    ).stem

    dataset = HyperspectralDataset()
    dataset.name = f'Hyperspectral Dataset - {measurement.label}'
    dataset.measurements = [measurement]
    dataset.figures = collect_dataset_figures(dataset.measurements)
    return dataset


def build_hyperspectral_dataset(
    source: Path,
    log,
    upload_root: Path | None = None,
    context=None,
) -> HyperspectralDataset:
    """Build a dataset from the selected ENVI header and its matching BIL file."""
    if context is not None:
        return _build_hyperspectral_dataset_from_context(source, context, log)

    source = Path(source)
    is_header_file = source.suffix.lower() == '.hdr'
    label_root = source.parent if is_header_file else source
    if is_header_file:
        root = upload_root or source.parent
        measurement = parse_hyperspectral_folder(
            source.parent,
            root,
            log,
            hdr_file=source,
        )
        measurements = [measurement] if measurement else []
    else:
        root = source
        measurements = []
        for folder in find_hyperspectral_folders(root):
            measurement = parse_hyperspectral_folder(folder, root, log)
            if measurement:
                measurements.append(measurement)

    dataset = HyperspectralDataset()
    dataset.name = f'Hyperspectral Dataset - {label_root.name}'
    dataset.measurements = measurements
    dataset.figures = collect_dataset_figures(measurements)
    return dataset


class HyperspectralRootParser(MatchingParser):
    """Parser for hyperspectral ENVI datasets."""

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger=None,
        child_archives=None,
    ) -> None:
        log = logger or logger_module
        root = Path(mainfile).parent
        dataset = build_hyperspectral_dataset(root, log)
        archive.data = dataset
        log.info('Parsed %d hyperspectral measurements', len(dataset.measurements))
