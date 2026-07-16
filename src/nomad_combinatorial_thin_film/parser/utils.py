import math

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ENVI_DTYPE_MAP = {
    '12': np.uint16,
    '4': np.float32,
    '5': np.float64,
    '2': np.int16,
}


def read_envi_hdr(path):
    """
    Read an ENVI .hdr file into a dictionary.

    Parameters
    ----------
    path : str
        Path to the .hdr file

    Returns
    -------
    dict
        Header metadata (keys are lowercase)
    """
    metadata = {}

    with open(path) as f:
        lines = f.readlines()

    key = None
    collecting = False
    buffer = []

    for line in lines:
        line = line.strip()

        if not line or line.upper() == 'ENVI':
            continue

        if collecting:
            buffer.append(line)
            if '}' in line:
                metadata[key] = ' '.join(buffer)
                collecting = False
                buffer = []
            continue

        if '=' in line:
            k, v = map(str.strip, line.split('=', 1))
            k = k.lower()

            if v.startswith('{') and not v.endswith('}'):
                key = k
                collecting = True
                buffer.append(v)
            else:
                metadata[k] = v

    return metadata


def read_bil(path, lines, samples, bands, dtype):
    """
    Read a BIL (Band Interleaved by Line) file.

    Parameters
    ----------
    path : str
        Path to .bil file
    lines, samples, bands : int
        Cube dimensions
    dtype : numpy dtype
        Data type from ENVI header

    Returns
    -------
    ndarray
        Data array with shape (lines, samples, bands)
    """
    data = np.fromfile(path, dtype=dtype)

    expected = lines * samples * bands
    if data.size != expected:
        raise ValueError(f'Size mismatch: expected {expected}, got {data.size}')

    # BIL order → (lines, bands, samples)
    data = data.reshape(lines, bands, samples)

    # Reorder → (lines, samples, bands)
    return np.transpose(data, (0, 2, 1))


class HyperspectralCube:
    """
    Container and analysis tools for hyperspectral datacubes.
    """

    def __init__(self, data, wavelengths, metadata=None):
        """
        Parameters
        ----------
        data : ndarray
            Shape (lines, samples, bands)
        wavelengths : ndarray
            Shape (bands,)
        metadata : dict, optional
            ENVI header metadata
        """
        self.data = data
        self.wavelengths = wavelengths
        self.metadata = metadata or {}

    # ------------------
    # Basic accessors
    # ------------------

    def band_index(self, wavelength_nm):
        """Return band index closest to a wavelength."""
        return int(np.abs(self.wavelengths - wavelength_nm).argmin())

    def band(self, wavelength_nm):
        """Return spatial image at given wavelength."""
        idx = self.band_index(wavelength_nm)
        return self.data[:, :, idx]

    def lines(self):
        """Number of scan lines (spatial Y)."""
        return self.data.shape[0]

    def spectrum(self, line, sample):
        """Return spectrum at a single pixel."""
        return self.data[line, sample, :]

    def mean_spectrum(self, roi=None):
        """
        Compute mean spectrum.

        roi : tuple or None
            (line_start, line_end, sample_start, sample_end)
        """
        if roi is None:
            return self.data.mean(axis=(0, 1))

        l1, l2, s1, s2 = roi
        return self.data[l1:l2, s1:s2, :].mean(axis=(0, 1))

    def plot_rgb(self, r_nm, g_nm, b_nm, title=None):
        """
        Interactive RGB composite with channel toggle buttons.
        """
        r = self.band_index(r_nm)
        g = self.band_index(g_nm)
        b = self.band_index(b_nm)

        rgb = np.stack(
            [
                self.data[:, :, r],
                self.data[:, :, g],
                self.data[:, :, b],
            ],
            axis=-1,
        ).astype(float)

        rgb /= rgb.max() + 1e-9
        rgb_uint8 = (255 * rgb).astype(np.uint8)

        fig = go.Figure()

        # RGB image
        fig.add_trace(go.Image(z=rgb_uint8, name='RGB'))

        # Individual channels (for toggling)
        fig.add_trace(go.Image(z=rgb_uint8[:, :, [0]], name='R', visible=False))
        fig.add_trace(go.Image(z=rgb_uint8[:, :, [1]], name='G', visible=False))
        fig.add_trace(go.Image(z=rgb_uint8[:, :, [2]], name='B', visible=False))

        fig.update_layout(
            title=title or f'RGB ({r_nm}/{g_nm}/{b_nm} nm)',
            xaxis_title='Samples',
            yaxis_title='Lines',
            yaxis_autorange='reversed',
            updatemenus=[
                dict(
                    type='buttons',
                    direction='right',
                    buttons=[
                        dict(
                            label='RGB',
                            method='update',
                            args=[{'visible': [True, False, False, False]}],
                        ),
                        dict(
                            label='R',
                            method='update',
                            args=[{'visible': [False, True, False, False]}],
                        ),
                        dict(
                            label='G',
                            method='update',
                            args=[{'visible': [False, False, True, False]}],
                        ),
                        dict(
                            label='B',
                            method='update',
                            args=[{'visible': [False, False, False, True]}],
                        ),
                    ],
                    pad={'r': 10, 't': 10},
                    showactive=True,
                )
            ],
        )

        return fig

    def _add_grid_lines(self, fig, n_rows, n_cols, lines, samples):
        row_edges = np.linspace(0, lines, n_rows + 1)
        col_edges = np.linspace(0, samples, n_cols + 1)

        for r in row_edges:
            fig.add_shape(
                type='line',
                x0=0,
                x1=samples,
                y0=r,
                y1=r,
                line=dict(color='cyan', width=1),
            )

        for c in col_edges:
            fig.add_shape(
                type='line',
                x0=c,
                x1=c,
                y0=0,
                y1=lines,
                line=dict(color='cyan', width=1),
            )

    def plot_wavelength_images(
        self, wavelength_list, max_cols=3, normalize=True, title='Wavelength images'
    ):
        """
        Interactive grid of single-band images.
        """
        n = len(wavelength_list)
        cols = min(max_cols, n)
        rows = math.ceil(n / cols)

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=[f'{wl:.1f} nm' for wl in wavelength_list],
        )

        for i, wl in enumerate(wavelength_list):
            r = i // cols + 1
            c = i % cols + 1

            img = self.band(wl).astype(float)
            if normalize:
                img /= img.max() + 1e-9

            fig.add_trace(
                go.Heatmap(z=img, colorscale='Gray', showscale=False), row=r, col=c
            )

        fig.update_layout(title=title, height=300 * rows, width=350 * cols)

        fig.update_yaxes(autorange='reversed')

        return fig

    def plot_grid_mean_spectra(
        self,
        n_rows,
        n_cols,
        image_band_nm=None,
        normalize=True,
        title='Grid mean spectra',
    ):
        """
        Interactive spatial grid + mean spectra per grid cell.
        """
        lines, samples, _ = self.data.shape

        # Background image
        if image_band_nm is None:
            image = self.data.mean(axis=2)
            img_title = 'Mean intensity'
        else:
            image = self.band(image_band_nm)
            img_title = f'{image_band_nm:.1f} nm'

        fig = make_subplots(
            rows=1,
            cols=2,
            column_widths=[0.45, 0.55],
            subplot_titles=(img_title, 'Mean spectra'),
        )

        # Image
        fig.add_trace(
            go.Heatmap(z=image, colorscale='Gray', showscale=False), row=1, col=1
        )

        row_edges = np.linspace(0, lines, n_rows + 1)
        col_edges = np.linspace(0, samples, n_cols + 1)

        cell = 1
        for i in range(n_rows):
            for j in range(n_cols):
                rs = slice(int(row_edges[i]), int(row_edges[i + 1]))
                cs = slice(int(col_edges[j]), int(col_edges[j + 1]))

                spectrum = self.data[rs, cs, :].mean(axis=(0, 1))
                if normalize:
                    spectrum /= spectrum.max() + 1e-9

                fig.add_trace(
                    go.Scatter(
                        x=self.wavelengths,
                        y=spectrum,
                        mode='lines',
                        name=f'Cell {cell}',
                    ),
                    row=1,
                    col=2,
                )

                # Grid cell label
                fig.add_annotation(
                    x=0.5 * (col_edges[j] + col_edges[j + 1]),
                    y=0.5 * (row_edges[i] + row_edges[i + 1]),
                    text=str(cell),
                    showarrow=False,
                    font=dict(color='yellow'),
                    bgcolor='black',
                    opacity=0.6,
                    row=1,
                    col=1,
                )

                cell += 1

        fig.update_yaxes(autorange='reversed', row=1, col=1)

        self._add_grid_lines(fig, n_rows, n_cols, lines, samples)
        fig.update_layout(
            title=title,
            xaxis2_title='Wavelength (nm)',
            yaxis2_title='Normalized intensity' if normalize else 'Intensity',
        )

        return fig

    def plot_3d_spectral_slice(
        self, line_index=None, normalize=False, title='3D Spectral Slice'
    ):
        """
        3D plot: spatial X × wavelength × intensity for one scan line.
        """
        if line_index is None:
            line_index = self.lines // 2

        slice_data = self.data[line_index, :, :]

        if normalize:
            slice_data = slice_data / (slice_data.max() + 1e-9)

        fig = go.Figure(
            data=[
                go.Surface(
                    z=slice_data.T,
                    x=np.arange(self.samples),
                    y=self.wavelengths,
                    colorscale='Viridis',
                )
            ]
        )

        fig.update_layout(
            title=title + f' (line {line_index})',
            scene=dict(
                xaxis_title='Spatial X (samples)',
                yaxis_title='Wavelength (nm)',
                zaxis_title='Normalized intensity',
            ),
            height=600,
        )

        return fig


if __name__ == '__main__':
    hdr = read_envi_hdr('cube1.bil.hdr')

    dtype = ENVI_DTYPE_MAP[hdr['data type']]

    wavelengths = np.array([float(w) for w in hdr['wavelength'].strip('{}').split(',')])

    cube_data = read_bil(
        'cube1.bil',
        lines=int(hdr['lines']),
        samples=int(hdr['samples']),
        bands=int(hdr['bands']),
        dtype=dtype,
    )

    cube = HyperspectralCube(cube_data, wavelengths, hdr)

    fig = cube.plot_rgb(650, 550, 450)
    fig.show()
    fig = cube.plot_wavelength_images(
        [350, 450, 550, 650, 750, 850, 950, 1050], max_cols=3
    )
    fig.show()
    fig = cube.plot_grid_mean_spectra(3, 3, normalize=False)
    fig.show()
    fig = cube.plot_grid_mean_spectra(6, 6, normalize=False)
    fig.show()
    fig = cube.plot_grid_mean_spectra(9, 9, normalize=False)
    fig.show()
    fig = cube.plot_3d_spectral_slice()
    fig.show()

# ============================================================
# Shared parser utilities
# ============================================================

import json
import re
from pathlib import Path

import pandas as pd
from PIL import Image
from nomad.datamodel.metainfo.plot import PlotlyFigure

from nomad_combinatorial_thin_film.plugin.image_plugin import (
    BoundingBox,
    ImageData,
    ImageDimensions,
    ImageExperimentRun,
    ImageMetadata,
    ImageVisualization,
    ManifestData,
    RegionOfInterest,
)
from nomad_combinatorial_thin_film.plugin.hyperspectral_plugin import (
    AcquisitionMetadata,
    CubeMetadata,
    HyperspectralMeasurement,
    HyperspectralRawData,
    HyperspectralAnalysis,
)

METADATA_NAMES = ('metadata.json',)
NPY_NAMES = ('image_raw.npy', 'raw_image.npy')
PNG_NAMES = ('image_preview.png', 'preview.png', 'image.png')
IMAGE_FOLDER_HINTS = ('image data', 'image_data', 'images', 'image')
TIMESTAMP_PATTERN = re.compile(r'^\d{8}_\d{6}$')


def relative_upload_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace('\\', '/')
    except ValueError:
        return str(path).replace('\\', '/')


def to_float(value) -> float:
    if isinstance(value, str):
        value = value.strip().replace(',', '.')
    return float(value)


def safe_float(value):
    try:
        return float(value)
    except Exception:
        return None


def safe_int(value):
    try:
        return int(float(value))
    except Exception:
        return None


def safe_bool(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value = value.strip().lower()
        if value in {'true', '1', 'yes'}:
            return True
        if value in {'false', '0', 'no'}:
            return False

    return None


# ============================================================
# Image parser utilities
# ============================================================


def find_synthesis_json(data_root: Path) -> Path | None:
    json_files = [
        path
        for path in data_root.glob('*.json')
        if path.name.lower() not in METADATA_NAMES
    ]
    if not json_files:
        return None

    preferred_terms = ('synth', 'synthesis', 'condition', 'conditions')
    for path in sorted(json_files):
        if any(term in path.stem.lower() for term in preferred_terms):
            return path

    return sorted(json_files)[0]


def find_image_folders(data_root: Path) -> list[Path]:
    folders: list[Path] = []

    for folder in sorted(path for path in data_root.iterdir() if path.is_dir()):
        if folder.name.startswith('.'):
            continue

        has_image_files = (
            find_metadata_file(folder) is not None
            or find_npy_file(folder) is not None
        )
        has_layout_hint = folder.name.lower() in IMAGE_FOLDER_HINTS
        has_timestamp_name = TIMESTAMP_PATTERN.match(folder.name) is not None

        if has_image_files or has_layout_hint or has_timestamp_name:
            folders.append(folder)

    return folders


def find_metadata_file(folder: Path) -> Path | None:
    for name in METADATA_NAMES:
        path = folder / name
        if path.exists():
            return path
    candidates = sorted(folder.glob('*metadata*.json'))
    return candidates[0] if candidates else None


def find_npy_file(folder: Path) -> Path | None:
    for name in NPY_NAMES:
        path = folder / name
        if path.exists():
            return path
    candidates = sorted(folder.glob('*image*.npy'))
    return candidates[0] if candidates else None


def find_png_file(folder: Path) -> Path | None:
    for name in PNG_NAMES:
        path = folder / name
        if path.exists():
            return path
    candidates = sorted(folder.glob('*.png'))
    return candidates[0] if candidates else None


def experiment_name(image_folder: Path) -> str:
    if image_folder.name.lower() in IMAGE_FOLDER_HINTS:
        return 'Image data'
    return f'Experiment {image_folder.name}'


def parse_manifest(csv_path: Path, log) -> ManifestData | None:
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            log.debug('Manifest CSV is empty: %s', csv_path)
            return None

        row = df.iloc[0]
        manifest = ManifestData()
        mapping = {
            'Date': 'Date',
            'Cu_source_power': 'Cu_source_power',
            'Sn_source_power': 'Sn_source_power',
            'Zn_source_power': 'Zn_source_power',
            'Pressure': 'Pressure',
            'Source_temperature': 'Source_temperature',
            'Process_temperature': 'Process_temperature',
            'Chamber_pressure': 'Chamber_pressure',
            'Process_time': 'Process_time',
            'Cooling_time': 'Cooling_time',
            'Cooling_rate': 'Cooling_rate',
        }

        for csv_col, field_name in mapping.items():
            if csv_col in row.index and pd.notna(row[csv_col]):
                set_manifest_value(manifest, field_name, row[csv_col], log)

        return manifest

    except Exception as exc:
        log.error('Error parsing manifest %s: %s', csv_path, str(exc))
        return None


def parse_synthesis_json(json_path: Path, log) -> ManifestData | None:
    try:
        with open(json_path) as file:
            data = json.load(file)

        manifest = ManifestData()
        mapping = {
            'date': 'Date',
            'Date': 'Date',
            'cu_source_power': 'Cu_source_power',
            'Cu_source_power': 'Cu_source_power',
            'sn_source_power': 'Sn_source_power',
            'Sn_source_power': 'Sn_source_power',
            'zn_source_power': 'Zn_source_power',
            'Zn_source_power': 'Zn_source_power',
            'pressure_mtorr': 'Pressure',
            'Pressure': 'Pressure',
            'source_temperature_degc': 'Source_temperature',
            'Source_temperature': 'Source_temperature',
            'process_temperature_degc': 'Process_temperature',
            'Process_temperature': 'Process_temperature',
            'chamber_pressure_mbar': 'Chamber_pressure',
            'Chamber_pressure': 'Chamber_pressure',
            'process_time_min': 'Process_time',
            'Process_time': 'Process_time',
            'cooling_time_min': 'Cooling_time',
            'Cooling_time': 'Cooling_time',
            'cooling_rate_degc_min': 'Cooling_rate',
            'Cooling_rate': 'Cooling_rate',
        }

        for json_key, field_name in mapping.items():
            if json_key in data:
                set_manifest_value(manifest, field_name, data[json_key], log)

        return manifest

    except Exception as exc:
        log.error('Error parsing synthesis JSON %s: %s', json_path, str(exc))
        return None


def set_manifest_value(manifest: ManifestData, field_name: str, value, log):
    if value in (None, '', '-'):
        return
    try:
        if field_name == 'Date':
            setattr(manifest, field_name, str(value))
        else:
            setattr(manifest, field_name, to_float(value))
    except (ValueError, TypeError):
        log.warning('Could not convert manifest field %s=%s', field_name, value)


def parse_metadata(json_path: Path, log) -> tuple[ImageMetadata | None, ImageData | None, dict]:
    try:
        with open(json_path) as file:
            data = json.load(file)

        metadata = ImageMetadata()
        metadata.timestamp = str(data.get('timestamp', ''))
        metadata.exposure_ms = to_float(data.get('exposure_ms', 0.0))
        metadata.gain = to_float(data.get('gain', 0))
        metadata.bit_depth = int(to_float(data.get('bit_depth', 8)))
        metadata.shape = data.get('shape', [])
        metadata.is_color = bool(data.get('is_color', False))
        metadata.min = to_float(data.get('min', 0))
        metadata.max = to_float(data.get('max', 255))

        image_data = extract_image_data(data)
        return metadata, image_data, data

    except Exception as exc:
        log.error('Error parsing metadata %s: %s', json_path, str(exc))
        return None, None, {}


def extract_image_data(metadata_dict: dict) -> ImageData:
    image_data = ImageData()

    shape = metadata_dict.get('shape', [])
    if isinstance(shape, list) and len(shape) >= 2:
        dimensions = ImageDimensions()
        dimensions.height = int(shape[0])
        dimensions.width = int(shape[1])
        dimensions.channels = int(shape[2]) if len(shape) > 2 else 1
        dimensions.bit_depth = int(to_float(metadata_dict.get('bit_depth', 8)))
        dimensions.is_color = bool(metadata_dict.get('is_color', False))
        dimensions.pixel_value_min = int(to_float(metadata_dict.get('min', 0)))
        dimensions.pixel_value_max = int(to_float(metadata_dict.get('max', 255)))
        image_data.dimensions = dimensions

    circular_roi = metadata_dict.get('circular_roi', {})
    if circular_roi:
        roi = RegionOfInterest()
        roi.center_x_px = to_float(circular_roi.get('center_x_px', 0))
        roi.center_y_px = to_float(circular_roi.get('center_y_px', 0))
        roi.radius_px = to_float(circular_roi.get('radius_px', 0))
        roi.square_crop_size_px = int(
            to_float(circular_roi.get('square_crop_size_px', 0))
        )

        bbox_data = circular_roi.get('bounding_box', {})
        if bbox_data:
            bbox = BoundingBox()
            bbox.x_min = int(to_float(bbox_data.get('x_min', 0)))
            bbox.y_min = int(to_float(bbox_data.get('y_min', 0)))
            bbox.x_max = int(to_float(bbox_data.get('x_max', 0)))
            bbox.y_max = int(to_float(bbox_data.get('y_max', 0)))
            bbox.width = int(to_float(bbox_data.get('width', 0)))
            bbox.height = int(to_float(bbox_data.get('height', 0)))
            roi.bounding_box = bbox

        image_data.roi = roi

    return image_data


def dimensions_from_npy(npy_path: Path, metadata_dict: dict, log) -> ImageDimensions | None:
    try:
        image_array = np.load(str(npy_path), mmap_mode='r')
        if len(image_array.shape) < 2:
            return None

        dimensions = ImageDimensions()
        dimensions.height = int(image_array.shape[0])
        dimensions.width = int(image_array.shape[1])
        dimensions.channels = int(image_array.shape[2]) if len(image_array.shape) > 2 else 1
        dimensions.bit_depth = int(to_float(metadata_dict.get('bit_depth', 8)))
        dimensions.is_color = dimensions.channels > 1
        dimensions.pixel_value_min = int(np.min(image_array))
        dimensions.pixel_value_max = int(np.max(image_array))
        return dimensions
    except Exception as exc:
        log.warning('Could not derive dimensions from %s: %s', npy_path, str(exc))
        return None


def convert_npy_to_png(npy_path: Path, log) -> Path | None:
    try:
        image_array = np.load(str(npy_path))
        if image_array.size == 0:
            log.warning('Image array is empty: %s', npy_path)
            return None

        if len(image_array.shape) == 3 and image_array.shape[2] >= 3:
            img_normalized = normalize_array(image_array[:, :, :3])
            img = Image.fromarray(img_normalized.astype(np.uint8), mode='RGB')
        elif len(image_array.shape) == 3 and image_array.shape[2] == 1:
            img_normalized = normalize_array(image_array[:, :, 0])
            img = Image.fromarray(img_normalized.astype(np.uint8), mode='L')
        elif len(image_array.shape) == 2:
            img_normalized = normalize_array(image_array)
            img = Image.fromarray(img_normalized.astype(np.uint8), mode='L')
        else:
            log.warning('Unsupported image shape: %s', image_array.shape)
            return None

        png_path = npy_path.parent / 'image_preview.png'
        img.save(str(png_path))
        return png_path

    except Exception as exc:
        log.error('Error converting NPY to PNG %s: %s', npy_path, str(exc))
        return None


def normalize_array(array: np.ndarray) -> np.ndarray:
    arr_min = array.min()
    arr_max = array.max()

    if arr_max == arr_min:
        return np.full_like(array, 128, dtype=np.float32)

    return (array - arr_min) / (arr_max - arr_min) * 255


def parse_image_folder(image_folder: Path, data_root: Path, log) -> ImageExperimentRun | None:
    metadata_path = find_metadata_file(image_folder)
    manifest_path = image_folder / 'manifest.csv'
    npy_path = find_npy_file(image_folder)
    png_path = find_png_file(image_folder)

    if not any((metadata_path, manifest_path.exists(), npy_path, png_path)):
        log.debug('Skipping folder without parseable image data: %s', image_folder)
        return None

    experiment = ImageExperimentRun()
    experiment.timestamp = image_folder.name
    experiment.name = experiment_name(image_folder)

    if manifest_path.exists():
        manifest = parse_manifest(manifest_path, log)
        if manifest:
            experiment.manifest_data = manifest

    metadata_dict = {}
    if metadata_path:
        metadata, image_data, metadata_dict = parse_metadata(metadata_path, log)
        if metadata:
            experiment.metadata = metadata
        if image_data:
            experiment.image = image_data

    if npy_path or png_path:
        if experiment.image is None:
            experiment.image = ImageData()

        if npy_path:
            experiment.image.image_array = relative_upload_path(npy_path, data_root)
            if experiment.image.dimensions is None:
                experiment.image.dimensions = dimensions_from_npy(
                    npy_path, metadata_dict, log
                )
            experiment.image.create_image_plot(npy_path, log)

        preview_path = png_path
        if preview_path is None and npy_path:
            preview_path = convert_npy_to_png(npy_path, log)

        if preview_path:
            preview_ref = relative_upload_path(preview_path, data_root)
            experiment.image.image_preview = preview_ref
            experiment.image.visualization = ImageVisualization()
            experiment.image.visualization.image_file = preview_ref
            log.info('Image preview available for %s: %s', image_folder.name, preview_ref)

    return experiment


# ============================================================
# Hyperspectral parser utilities
# ============================================================


def collect_dataset_figures(measurements: list[HyperspectralMeasurement]):
    figures = []

    for measurement in measurements:
        visualization = measurement.visualization
        if visualization is None or not visualization.figures:
            continue

        for figure in visualization.figures:
            label = figure.label
            if len(measurements) > 1 and measurement.label:
                label = f'{measurement.label} - {label}'

            figures.append(
                PlotlyFigure(
                    label=label,
                    index=figure.index,
                    open=figure.open,
                    figure=figure.figure,
                )
            )

    return figures


def find_hyperspectral_folders(root: Path) -> list[Path]:
    folders = []

    if find_hdr_file(root) and find_bil_file(root):
        folders.append(root)

    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue

        if list(folder.glob('*.hdr')):
            folders.append(folder)

    return folders


def find_hdr_file(folder: Path) -> Path | None:
    files = list(folder.glob('*.hdr'))
    return files[0] if files else None


def find_bil_file(folder: Path, hdr_file: Path | None = None) -> Path | None:
    if hdr_file is not None and hdr_file.name.endswith('.bil.hdr'):
        matching_bil = folder / hdr_file.name.removesuffix('.hdr')
        if matching_bil.exists():
            return matching_bil

    files = list(folder.glob('*.bil'))
    return files[0] if files else None


def extract_wavelengths(hdr) -> np.ndarray:
    values = hdr['wavelength']
    values = values.strip('{}')
    return np.array([float(v) for v in values.split(',')])


def nearest_band(wavelengths, wavelength):
    return int(np.abs(wavelengths - wavelength).argmin())


def build_cube_metadata(hdr, wavelengths) -> CubeMetadata:
    metadata = CubeMetadata()
    metadata.lines = int(hdr['lines'])
    metadata.samples = int(hdr['samples'])
    metadata.bands = int(hdr['bands'])
    metadata.wavelength = wavelengths.tolist()
    metadata.interleave = hdr.get('interleave', '')
    metadata.data_type = hdr.get('data type', '')
    metadata.wavelength_min_nm = float(wavelengths.min())
    metadata.wavelength_max_nm = float(wavelengths.max())
    return metadata


def build_acquisition_metadata(hdr) -> AcquisitionMetadata:
    metadata = AcquisitionMetadata()
    metadata.interleave = hdr.get('interleave')
    metadata.data_type = hdr.get('data type')
    metadata.sample_binning = safe_int(hdr.get('sample binning'))
    metadata.spectral_binning = safe_int(hdr.get('spectral binning'))
    metadata.line_binning = safe_int(hdr.get('line binning'))
    metadata.shutter = safe_float(hdr.get('shutter'))
    metadata.gain = safe_float(hdr.get('gain'))
    metadata.framerate = safe_float(hdr.get('framerate'))
    metadata.temperature = safe_float(hdr.get('temperature'))
    metadata.imager_serial_number = hdr.get('imager serial number')
    metadata.rotation = hdr.get('rotation')
    metadata.pixel_size = safe_float(hdr.get('pixel size'))
    metadata.byte_order = hdr.get('byte order')
    metadata.header_offset = safe_int(hdr.get('header offset', 0))
    metadata.flip_radiometric_calibration = safe_bool(
        hdr.get('flip radiometric calibration')
    )
    metadata.wavelength_unit = hdr.get('wavelength units')
    metadata.label = hdr.get('label')
    return metadata


def create_npy(folder: Path, cube: np.ndarray) -> Path:
    npy_path = folder / 'cube.npy'
    np.save(npy_path, cube.astype(np.float32))
    return npy_path


def create_rgb_preview(folder: Path, cube: np.ndarray, wavelengths: np.ndarray, log) -> Path | None:
    try:
        r = nearest_band(wavelengths, 650)
        g = nearest_band(wavelengths, 550)
        b = nearest_band(wavelengths, 450)

        rgb = np.stack(
            [cube[:, :, r], cube[:, :, g], cube[:, :, b]],
            axis=-1,
        ).astype(np.float32)
        rgb /= rgb.max() + 1e-9
        rgb = (rgb * 255).astype(np.uint8)

        preview_path = folder / 'rgb_preview.png'
        Image.fromarray(rgb).save(preview_path)
        return preview_path

    except Exception as exc:
        log.warning('Could not create RGB preview: %s', exc)
        return None


def parse_hyperspectral_folder(folder: Path, root: Path, log) -> HyperspectralMeasurement | None:
    hdr_file = find_hdr_file(folder)
    bil_file = find_bil_file(folder, hdr_file)

    if hdr_file is None or bil_file is None:
        return None

    try:
        hdr = read_envi_hdr(str(hdr_file))
        wavelengths = extract_wavelengths(hdr)
        dtype = ENVI_DTYPE_MAP[str(hdr['data type'])]

        cube = read_bil(
            str(bil_file),
            lines=int(hdr['lines']),
            samples=int(hdr['samples']),
            bands=int(hdr['bands']),
            dtype=dtype,
        )

        npy_file = create_npy(folder, cube)
        preview_file = create_rgb_preview(folder, cube, wavelengths, log)

        measurement = HyperspectralMeasurement()
        measurement.acquisition_metadata = build_acquisition_metadata(hdr)
        measurement.cube_metadata = build_cube_metadata(hdr, wavelengths)

        raw_data = HyperspectralRawData()
        raw_data.hdr_file = relative_upload_path(hdr_file, root)
        raw_data.bil_file = relative_upload_path(bil_file, root)
        raw_data.cube_npy = relative_upload_path(npy_file, root)

        if preview_file:
            raw_data.rgb_preview = relative_upload_path(preview_file, root)

        measurement.raw_data = raw_data
        measurement.visualization = HyperspectralAnalysis()
        measurement.visualization.create_analysis_figures(npy_file, hdr_file, log)
        measurement.label = folder.name
        return measurement

    except Exception as exc:
        log.error('Error parsing hyperspectral folder %s : %s', folder, exc)
        return None


