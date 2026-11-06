"""NOMAD parser for spatially resolved ASC and XRDML measurements."""

import io
import logging
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
from nomad.datamodel import EntryArchive
from nomad.parsing.parser import MatchingParser
from scipy.signal import (
    find_peaks,
    peak_widths,
    savgol_filter,
)

from nomad_combinatorial_thin_film.plugin.xrd import (
    XRDPattern,
    XRDPeak,
    XRDRun,
)

logger = logging.getLogger(__name__)


# ============================================================
# 1. Position extraction
# ============================================================

POSITION_RE = re.compile(
    r"phi\s*(-?\d+(?:\.\d+)?)\s*"
    r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*"
    r"(-?\d+(?:\.\d+)?)\s*\)",
    re.IGNORECASE,
)


def parse_position(filename):
    """Extract phi, x and y coordinates from a filename."""

    match = POSITION_RE.search(str(filename))

    if not match:
        raise ValueError(
            f"Cannot extract measurement coordinates from {filename}. "
            "Expected a filename containing phi0(0,-15)."
        )

    phi, x, y = match.groups()

    return (
        int(round(float(phi))),
        float(x),
        float(y),
    )


def position_key(position):
    """Convert position coordinates into a readable label."""

    phi, x, y = position

    return f"phi{phi}({x:g},{y:g})"


def position_sort_key(position):
    """Use the same spatial ordering as the original analysis."""

    phi, x, y = position

    return phi, y, x


# ============================================================
# 2. Clean XRD data
# ============================================================


def clean_xy(two_theta, intensity, filename, uncertainty=None):
    """Validate, sort and clean experimental XRD arrays."""

    x = np.asarray(two_theta, dtype=float).ravel()
    y = np.asarray(intensity, dtype=float).ravel()

    if x.size != y.size:
        raise ValueError(f"{filename}: 2theta/intensity length mismatch.")

    if uncertainty is not None:

        uncertainty = np.asarray(
            uncertainty,
            dtype=float,
        ).ravel()

        if uncertainty.size != x.size:
            raise ValueError(f"{filename}: uncertainty array length mismatch.")

    valid = np.isfinite(x) & np.isfinite(y)

    x = x[valid]
    y = y[valid]

    if uncertainty is not None:
        uncertainty = uncertainty[valid]

    if len(x) < 2:
        raise ValueError(f"{filename}: insufficient valid XRD data points.")

    # Sort by 2theta.
    order = np.argsort(x, kind="stable")

    x = x[order]
    y = y[order]

    if uncertainty is not None:
        uncertainty = uncertainty[order]

    # Remove duplicate 2theta positions.
    x_unique, unique_indices = np.unique(
        x,
        return_index=True,
    )

    x = x_unique
    y = y[unique_indices]

    if uncertainty is not None:
        uncertainty = uncertainty[unique_indices]

    if len(x) < 2:
        raise ValueError(f"{filename}: insufficient unique 2theta values.")

    return {
        "two_theta": x,
        "intensity": y,
        "uncertainty": uncertainty,
    }


# ============================================================
# 3. ASC reader
# ============================================================


def read_asc(content, filename):
    """Read a two- or three-column ASC XRD file."""

    array = np.loadtxt(io.BytesIO(content))

    if array.ndim == 1:
        array = np.atleast_2d(array)

    if array.ndim != 2 or array.shape[1] < 2:
        raise ValueError(f"Invalid ASC file: {filename}")

    two_theta = array[:, 0]
    intensity = array[:, 1]

    uncertainty = array[:, 2] if array.shape[1] >= 3 else None

    return clean_xy(
        two_theta,
        intensity,
        filename,
        uncertainty,
    )


# ============================================================
# 4. XRDML reader
# ============================================================


def local_name(element):
    """Return an XML tag without its namespace."""

    return element.tag.rsplit("}", 1)[-1].lower()


def find_all(element, name):
    """Find XML elements using namespace-independent names."""

    return [node for node in element.iter() if local_name(node) == name.lower()]


def parse_float_list(text):
    """Convert whitespace- or comma-separated numbers into an array."""

    if not text:
        return np.array([], dtype=float)

    return np.fromstring(
        text.replace(",", " "),
        sep=" ",
        dtype=float,
    )


def read_xrdml(content, filename):
    """Read a PANalytical XRDML scan."""

    root = ET.fromstring(content)

    blocks = find_all(
        root,
        "dataPoints",
    )

    if not blocks:
        raise ValueError(f"No dataPoints element found in {filename}.")

    if len(blocks) > 1:
        logger.warning(
            "%s contains multiple dataPoints blocks. "
            "The first block will be read, matching the original reader.",
            filename,
        )

    block = blocks[0]

    intensity_nodes = find_all(block, "intensities") or find_all(block, "counts")

    if not intensity_nodes:
        raise ValueError(f"No intensity array found in {filename}.")

    intensity = parse_float_list(intensity_nodes[0].text)

    if len(intensity) == 0:
        raise ValueError(f"Cannot parse intensity array in {filename}.")

    # Identify the 2theta axis.
    axis_node = None

    for node in find_all(block, "positions"):

        axis = node.attrib.get("axis", "").lower().replace(" ", "")

        if axis in ("2theta", "2-theta", "twotheta"):
            axis_node = node
            break

    if axis_node is None:
        raise ValueError(f"Cannot identify the 2theta axis in {filename}.")

    # Some XRDML files contain an explicit list of positions.
    explicit = find_all(
        axis_node,
        "listPositions",
    )

    if explicit and explicit[0].text:

        two_theta = parse_float_list(explicit[0].text)

    else:

        starts = find_all(
            axis_node,
            "startPosition",
        )

        ends = find_all(
            axis_node,
            "endPosition",
        )

        if not starts or not ends:
            raise ValueError(f"Missing 2theta start/end positions in {filename}.")

        start = float(starts[0].text)
        end = float(ends[0].text)

        two_theta = np.linspace(
            start,
            end,
            len(intensity),
        )

    return clean_xy(
        two_theta,
        intensity,
        filename,
    )


# ============================================================
# 5. Read individual files
# ============================================================


def read_one(content, filename):
    """Select the reader according to the original file extension."""

    extension = Path(filename).suffix.lower()

    if extension == ".asc":
        return read_asc(content, filename)

    if extension == ".xrdml":
        return read_xrdml(content, filename)

    raise ValueError(f"Unsupported XRD file format: {filename}")


# ============================================================
# 6. Load ZIP archive or individual XRD file
# ============================================================


def load_xrd_files(mainfile):
    """
    Load spatially resolved XRD measurements from one ZIP archive.

    Workflow:
        1. Validate that the mainfile is a ZIP archive.
        2. Inspect the ZIP contents.
        3. Find ASC and XRDML measurement files.
        4. Extract their contents in memory.
        5. Read and process each measurement.
        6. Return all patterns as records for one NOMAD entry.

    ASC files are preferred if duplicate spatial positions exist.
    """

    mainfile = Path(mainfile)

    # --------------------------------------------------------
    # 1. Validate ZIP archive
    # --------------------------------------------------------

    if not zipfile.is_zipfile(mainfile):
        raise ValueError(
            f"Expected a ZIP archive as the NOMAD mainfile, "
            f"but received: {mainfile.name}"
        )

    records = []

    # --------------------------------------------------------
    # 2. Open ZIP and find measurement files
    # --------------------------------------------------------

    with zipfile.ZipFile(mainfile, "r") as archive:

        candidates = {}

        filenames = [
            name
            for name in archive.namelist()
            if not name.endswith("/")
            and not name.startswith("__MACOSX/")
            and Path(name).suffix.lower() in (".asc", ".xrdml")
        ]

        logger.info(
            "Found %d candidate XRD files in ZIP archive %s.",
            len(filenames),
            mainfile.name,
        )

        if not filenames:
            raise ValueError(
                f"No ASC or XRDML files found inside {mainfile.name}."
            )

        # ----------------------------------------------------
        # 3. Group files by spatial measurement position
        # ----------------------------------------------------

        for filename in filenames:

            basename = Path(filename).name

            position = parse_position(basename)

            candidates.setdefault(position, []).append(filename)

        # ----------------------------------------------------
        # 4. Read each selected measurement from ZIP
        # ----------------------------------------------------

        for position in sorted(
            candidates,
            key=position_sort_key,
        ):

            options = candidates[position]

            # Prefer ASC over XRDML if both exist.
            selected = sorted(
                options,
                key=lambda name: (
                    0 if Path(name).suffix.lower() == ".asc" else 1,
                    name.lower(),
                ),
            )[0]

            logger.info(
                "Reading measurement from ZIP: %s",
                selected,
            )

            # Read the selected ZIP member into memory.
            content = archive.read(selected)

            # Select the correct reader using the member extension.
            data = read_one(
                content,
                Path(selected).name,
            )

            records.append(
                {
                    "position": position,
                    "position_label": position_key(position),
                    "source_filename": Path(selected).name,
                    **data,
                }
            )

    # --------------------------------------------------------
    # 5. Validate and sort measurements
    # --------------------------------------------------------

    if not records:
        raise ValueError(
            f"No valid XRD measurements found in {mainfile.name}."
        )

    records.sort(
        key=lambda item: position_sort_key(item["position"])
    )

    logger.info(
        "Successfully loaded %d spatial XRD patterns from ZIP archive %s.",
        len(records),
        mainfile.name,
    )

    input_format = "ZIP archive containing ASC/XRDML files"

    return records, input_format

# ============================================================
# 7. Peak detection
# ============================================================

DEFAULT_PEAK_CONFIG = {
    "smoothing_enabled": True,
    "smoothing_window": 7,
    "smoothing_polyorder": 2,
    "prominence_fraction": 0.03,
    "minimum_prominence": 0.0,
    "minimum_distance_deg": 0.15,
    "minimum_width_deg": 0.0,
}


def smooth_xrd_pattern(
    intensity,
    window_length=7,
    polyorder=2,
):
    """Apply the Savitzky-Golay filter."""

    intensity = np.asarray(
        intensity,
        dtype=float,
    )

    if len(intensity) < 3:
        return intensity.copy()

    if window_length % 2 == 0:
        window_length += 1

    max_window = len(intensity)

    if max_window % 2 == 0:
        max_window -= 1

    window_length = min(
        window_length,
        max_window,
    )

    if window_length <= polyorder:
        return intensity.copy()

    return savgol_filter(
        intensity,
        window_length=window_length,
        polyorder=polyorder,
        mode="interp",
    )


def detect_peaks(
    x,
    y,
    detection_config=None,
):
    """
    Detect peaks using the same approach as the original code.

    Peak detection is performed on smoothed intensity.
    Original measured intensity is retained in the peak results.
    """

    config = {
        **DEFAULT_PEAK_CONFIG,
        **(detection_config or {}),
    }

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    # --------------------------------------------------------
    # Clean and sort input
    # --------------------------------------------------------

    valid = np.isfinite(x) & np.isfinite(y)

    x = x[valid]
    y = y[valid]

    if len(x) < 3:
        return []

    order = np.argsort(x)

    x = x[order]
    y = y[order]

    x, unique_indices = np.unique(
        x,
        return_index=True,
    )

    y = y[unique_indices]

    if len(x) < 3:
        return []

    # --------------------------------------------------------
    # Processing
    # --------------------------------------------------------

    y_processed = y.copy()

    background = float(config.get("subtract_constant_background", 0.0))

    y_processed -= background

    if config.get("clip_negative_after_background", True):
        y_processed = np.clip(
            y_processed,
            0,
            None,
        )

    normalization = str(config.get("normalization", "none")).lower()

    if normalization == "max":

        maximum = np.nanmax(y_processed)

        if maximum > 0:
            y_processed = y_processed / maximum

    elif normalization != "none":

        raise ValueError("Normalization must be 'none' or 'max'.")

    # --------------------------------------------------------
    # Smoothing
    # --------------------------------------------------------

    if config["smoothing_enabled"]:

        smoothed_y = smooth_xrd_pattern(
            y_processed,
            window_length=int(config["smoothing_window"]),
            polyorder=int(config["smoothing_polyorder"]),
        )

    else:
        smoothed_y = y_processed.copy()

    intensity_range = float(np.ptp(smoothed_y))

    if not np.isfinite(intensity_range) or intensity_range <= 0:
        return []

    # --------------------------------------------------------
    # Detection parameters
    # --------------------------------------------------------

    step_size = float(np.median(np.diff(x)))

    if not np.isfinite(step_size) or step_size <= 0:
        return []

    prominence_fraction = float(config["prominence_fraction"])

    minimum_prominence = float(config["minimum_prominence"])

    prominence_threshold = max(
        intensity_range * prominence_fraction,
        minimum_prominence,
    )

    minimum_distance_deg = float(config["minimum_distance_deg"])

    minimum_distance_samples = max(
        1,
        int(np.ceil(minimum_distance_deg / step_size)),
    )

    # --------------------------------------------------------
    # Find peaks
    # --------------------------------------------------------

    peaks, properties = find_peaks(
        smoothed_y,
        prominence=prominence_threshold,
        distance=minimum_distance_samples,
    )

    if len(peaks) == 0:
        return []

    # --------------------------------------------------------
    # Peak widths
    # --------------------------------------------------------

    widths, _, left_ips, right_ips = peak_widths(
        smoothed_y,
        peaks,
        rel_height=0.5,
    )

    left_positions = np.interp(
        left_ips,
        np.arange(len(x)),
        x,
    )

    right_positions = np.interp(
        right_ips,
        np.arange(len(x)),
        x,
    )

    width_degrees = right_positions - left_positions

    relative_prominence = properties["prominences"] / intensity_range

    # --------------------------------------------------------
    # Construct results
    # --------------------------------------------------------

    minimum_width_deg = float(config["minimum_width_deg"])

    results = []

    for index, peak_index in enumerate(peaks):

        width = float(width_degrees[index])

        if width < minimum_width_deg:
            continue

        results.append(
            {
                "two_theta_deg": float(x[peak_index]),
                "intensity": float(y_processed[peak_index]),
                "smoothed_intensity": float(smoothed_y[peak_index]),
                "prominence": float(properties["prominences"][index]),
                "relative_prominence": float(relative_prominence[index]),
                "width_deg": width,
                "width_samples": float(widths[index]),
                "left_width_deg": float(left_positions[index]),
                "right_width_deg": float(right_positions[index]),
            }
        )

    return results


# ============================================================
# 8. Create NOMAD peak sections
# ============================================================


def create_peak_sections(peak_results):
    """Convert peak dictionaries into NOMAD subsections."""

    output = []

    for result in peak_results:

        peak = XRDPeak()

        peak.two_theta_deg = result["two_theta_deg"]
        peak.intensity = result["intensity"]
        peak.smoothed_intensity = result["smoothed_intensity"]
        peak.prominence = result["prominence"]
        peak.relative_prominence = result["relative_prominence"]
        peak.width_deg = result["width_deg"]
        peak.width_samples = result["width_samples"]
        peak.left_width_deg = result["left_width_deg"]
        peak.right_width_deg = result["right_width_deg"]

        output.append(peak)

    return output


# ============================================================
# 9. Create NOMAD XRD pattern sections
# ============================================================


def create_pattern_sections(
    records,
    detection_config,
):
    """Create all spatial patterns and their detected peaks."""

    output = []
    total_peaks = 0

    for record in records:

        pattern = XRDPattern()

        phi, x_mm, y_mm = record["position"]

        pattern.source_filename = record["source_filename"]
        pattern.position_label = record["position_label"]

        pattern.phi_deg = float(phi)
        pattern.x_mm = float(x_mm)
        pattern.y_mm = float(y_mm)

        pattern.two_theta_deg = np.asarray(
            record["two_theta"],
            dtype=float,
        )

        pattern.intensity = np.asarray(
            record["intensity"],
            dtype=float,
        )

        if record["uncertainty"] is not None:

            pattern.uncertainty = np.asarray(
                record["uncertainty"],
                dtype=float,
            )

        peak_results = detect_peaks(
            record["two_theta"],
            record["intensity"],
            detection_config,
        )

        pattern.peaks = create_peak_sections(peak_results)

        total_peaks += len(peak_results)

        logger.info(
            "%s: detected %d peaks.",
            record["position_label"],
            len(peak_results),
        )

        output.append(pattern)

    return output, total_peaks


# ============================================================
# 10. Create complete NOMAD XRD entry
# ============================================================


def create_xrd_run(
    filename,
    records,
    input_format,
    condition_label=None,
):
    """Build the complete NOMAD XRD experiment entry."""

    detection_config = DEFAULT_PEAK_CONFIG.copy()

    patterns, total_peaks = create_pattern_sections(
        records,
        detection_config,
    )

    run = XRDRun()

    # Use the ZIP filename as the sample/experiment name.
    # Example: GI-XRD_Combi_ZnCu_10min.zip
    # becomes: GI-XRD_Combi_ZnCu_10min

    sample_name = Path(filename).stem

    run.name = sample_name
    run.source_filename = Path(filename).name
    run.condition_label = condition_label or sample_name
    run.input_format = input_format

    run.number_of_patterns = len(patterns)
    run.number_of_detected_peaks = total_peaks

    run.peak_detection_enabled = True

    run.smoothing_enabled = detection_config["smoothing_enabled"]
    run.smoothing_window = detection_config["smoothing_window"]
    run.smoothing_polyorder = detection_config["smoothing_polyorder"]

    run.prominence_fraction = detection_config["prominence_fraction"]
    run.minimum_prominence = detection_config["minimum_prominence"]
    run.minimum_distance_deg = detection_config["minimum_distance_deg"]
    run.minimum_width_deg = detection_config["minimum_width_deg"]

    run.patterns = patterns

    # Generate NOMAD visualizations.
    run.plot()

    return run


# ============================================================
# 11. NOMAD parser
# ============================================================


class XRDParser(MatchingParser):
    """Parser for spatially resolved ASC and XRDML measurements."""

    def parse(
        self,
        mainfile,
        archive: EntryArchive,
        logger=None,
        child_archives=None,
    ):

        log = logger or logging.getLogger(__name__)

        log.info(
            "Reading XRD measurement: %s",
            mainfile,
        )

        records, input_format = load_xrd_files(mainfile)

        log.info(
            "Loaded %d spatial XRD patterns.",
            len(records),
        )

        run = create_xrd_run(
            filename=mainfile,
            records=records,
            input_format=input_format,
        )

        archive.data = run

        log.info(
            "Successfully parsed XRD experiment: %s",
            run.source_filename,
        )

        log.info(
            "Total spatial patterns: %d; detected peaks: %d.",
            run.number_of_patterns,
            run.number_of_detected_peaks,
        )
