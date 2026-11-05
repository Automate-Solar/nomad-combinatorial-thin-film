
"""NOMAD parser for PicoLog sulfurization PLW measurements."""

import configparser
import logging
import struct

from pathlib import Path

import numpy as np

from nomad.datamodel import EntryArchive
from nomad.parsing.parser import MatchingParser

from nomad_combinatorial_thin_film.plugin.sulfurization import (
    SulfurizationChannel,
    SulfurizationHoldingPeriod,
    SulfurizationRun,
)


logger = logging.getLogger(__name__)


# ============================================================
# 1. Analysis settings
# ============================================================

TARGET_TEMPERATURE = 325.0
TEMPERATURE_TOLERANCE = 2.0
MIN_HOLD_DURATION_S = 60.0

HOLD_CHANNEL = "furnace"


# PicoLog time-unit conversion to seconds.
UNIT_TO_SECONDS = {
    0: 1e-15,
    4: 1e-3,
    5: 1.0,
    6: 60.0,
    7: 3600.0,
}


# ============================================================
# 2. Read PicoLog PLW file
# ============================================================

def read_plw(filename):
    """
    Read a PicoLog for Windows PLW file.

    Returns
    -------
    metadata : dict
        File-header information.
    time_data : numpy.ndarray
        Elapsed time in seconds.
    channels : list[dict]
        Channel information, including name, unit and values.
    """

    filename = Path(filename)
    raw = filename.read_bytes()

    if len(raw) < 586:
        raise ValueError(
            "PLW file is too small to contain a valid header."
        )

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    header_size = struct.unpack_from(
        "<H", raw, 0
    )[0]

    signature = raw[2:42].split(
        b"\0", 1
    )[0].decode(
        "ascii",
        errors="replace",
    )

    if "PicoLog for Windows" not in signature:

        raise ValueError(
            "Not a valid PicoLog PLW file."
        )

    version, n_channels = struct.unpack_from(
        "<II",
        raw,
        42,
    )

    if n_channels < 1:
        raise ValueError(
            "PLW file contains no measurement channels."
        )

    channel_ids = struct.unpack_from(
        f"<{n_channels}H",
        raw,
        50,
    )

    (
        sample_number,
        n_samples,
        max_samples,
        interval,
        time_units,
    ) = struct.unpack_from(
        "<IIIIH",
        raw,
        550,
    )

    sample_size = struct.unpack_from(
        "<I",
        raw,
        578,
    )[0]

    settings_size = struct.unpack_from(
        "<I",
        raw,
        582,
    )[0]

    # --------------------------------------------------------
    # Validate header and data boundaries
    # --------------------------------------------------------

    if header_size < 586 or header_size > len(raw):
        raise ValueError(
            f"Invalid PLW header size: {header_size}"
        )

    if settings_size <= 0 or settings_size > len(raw):
        raise ValueError(
            f"Invalid PLW settings size: {settings_size}"
        )

    settings_start = len(raw) - settings_size
    data_start = header_size

    if settings_start < data_start:
        raise ValueError(
            "PLW settings overlap the measurement data."
        )

    expected_sample_size = 4 + 4 * n_channels

    if sample_size != expected_sample_size:

        raise ValueError(
            f"Unexpected sample size: {sample_size}; "
            f"expected {expected_sample_size}."
        )

    available_bytes = settings_start - data_start
    required_bytes = n_samples * sample_size

    if available_bytes < required_bytes:

        raise ValueError(
            "Incomplete PLW measurement data. "
            f"Required {required_bytes} bytes, "
            f"available {available_bytes} bytes."
        )

    # --------------------------------------------------------
    # Decode embedded configuration
    # --------------------------------------------------------

    settings = raw[settings_start:].decode(
        "latin-1",
        errors="replace",
    )

    if not settings.lstrip().startswith("["):
        settings = "[Sampling]\n" + settings

    config = configparser.ConfigParser(
        interpolation=None,
        strict=False,
    )

    config.optionxform = str

    config.read_string(settings)

    # --------------------------------------------------------
    # Extract channel names and units
    # --------------------------------------------------------

    channels = []

    for channel_id in channel_ids:

        section = f"Parameter {channel_id}"

        name = config.get(
            section,
            "Name",
            fallback=f"Channel_{channel_id}",
        ).strip()

        unit = (
            config.get(section, "ScaledUnits", fallback=None)
            or config.get(section, "UserUnits", fallback=None)
            or config.get(section, "InputUnits", fallback="")
        ).strip()

        channels.append(
            {
                "channel_id": int(channel_id),
                "name": name,
                "unit": unit,
                "values": [],
            }
        )

    # --------------------------------------------------------
    # Convert time units
    # --------------------------------------------------------

    seconds_per_unit = UNIT_TO_SECONDS.get(
        time_units
    )

    if seconds_per_unit is None:

        raise ValueError(
            f"Unsupported PicoLog time-unit code: {time_units}"
        )

    # --------------------------------------------------------
    # Decode measurement samples
    # --------------------------------------------------------

    time_data = np.empty(
        n_samples,
        dtype=np.float64,
    )

    values = np.empty(
        (n_samples, n_channels),
        dtype=np.float64,
    )

    for index in range(n_samples):

        offset = data_start + index * sample_size

        timestamp = struct.unpack_from(
            "<I",
            raw,
            offset,
        )[0]

        sample_values = struct.unpack_from(
            f"<{n_channels}f",
            raw,
            offset + 4,
        )

        time_data[index] = (
            timestamp * interval * seconds_per_unit
        )

        values[index, :] = sample_values

    # --------------------------------------------------------
    # Attach channel values
    # --------------------------------------------------------

    for channel_index, channel in enumerate(channels):

        channel["values"] = values[
            :,
            channel_index,
        ]

    extra_bytes = available_bytes - required_bytes

    #if extra_bytes:
    #    logger.warning(
    #        "%d additional bytes were not included in PLW samples.",
    #        extra_bytes,
    #    )

    metadata = {
        "signature": signature,
        "version": int(version),
        "sample_number": int(sample_number),
        "n_channels": int(n_channels),
        "n_samples": int(n_samples),
        "max_samples": int(max_samples),
        "interval": int(interval),
        "time_units": int(time_units),
        "sample_size": int(sample_size),
        "settings_size": int(settings_size),
        "channel_ids": [int(value) for value in channel_ids],
    }

    return metadata, time_data, channels


# ============================================================
# 3. Holding-period detection
# ============================================================

def detect_holding_period(
    time_data,
    channels,
    target_temperature=TARGET_TEMPERATURE,
    tolerance=TEMPERATURE_TOLERANCE,
    minimum_duration=MIN_HOLD_DURATION_S,
    hold_channel=HOLD_CHANNEL,
):
    """
    Identify continuous intervals within the temperature tolerance.

    The longest qualifying stable interval is selected.
    """

    channel_lookup = {
        channel["name"]: channel
        for channel in channels
    }

    if hold_channel not in channel_lookup:

        raise ValueError(
            f"Cannot find holding channel '{hold_channel}'. "
            f"Available channels: {list(channel_lookup)}"
        )

    furnace = np.asarray(
        channel_lookup[hold_channel]["values"],
        dtype=float,
    )

    stable = (
        np.isfinite(furnace)
        & (
            np.abs(furnace - target_temperature)
            <= tolerance
        )
    )

    # --------------------------------------------------------
    # Find continuous stable regions
    # --------------------------------------------------------

    regions = []

    start = None

    for index, is_stable in enumerate(stable):

        if is_stable and start is None:
            start = index

        elif not is_stable and start is not None:

            regions.append(
                (start, index - 1)
            )

            start = None

    if start is not None:

        regions.append(
            (start, len(stable) - 1)
        )

    # --------------------------------------------------------
    # Keep sufficiently long regions
    # --------------------------------------------------------

    valid_regions = []

    for first, last in regions:

        duration = (
            time_data[last] - time_data[first]
        )

        if duration >= minimum_duration:

            valid_regions.append(
                (first, last, duration)
            )

    if not valid_regions:
        return None

    # Select the longest stable interval.
    first, last, duration = max(
        valid_regions,
        key=lambda item: item[2],
    )

    return {
        "first": first,
        "last": last,
        "duration_s": float(duration),
        "start_time_s": float(time_data[first]),
        "end_time_s": float(time_data[last]),
    }


# ============================================================
# 4. Calculate temperature stability
# ============================================================

def calculate_stability(
    channels,
    first,
    last,
):
    """
    Calculate statistics for every channel during the selected interval.

    Uses sample standard deviation (ddof=1), matching the original
    statistics.stdev implementation.
    """

    results = {}

    for channel in channels:

        name = channel["name"]

        selected = np.asarray(
            channel["values"][first:last + 1],
            dtype=float,
        )

        selected = selected[np.isfinite(selected)]

        if len(selected) == 0:
            continue

        mean_value = float(np.mean(selected))

        std_value = (
            float(np.std(selected, ddof=1))
            if len(selected) > 1
            else 0.0
        )

        minimum = float(np.min(selected))
        maximum = float(np.max(selected))

        results[name] = {
            "mean": mean_value,
            "std": std_value,
            "minimum": minimum,
            "maximum": maximum,
            "range": maximum - minimum,
        }

    return results


# ============================================================
# 5. Build NOMAD channel sections
# ============================================================

def create_channel_sections(
    channels,
    stability_results,
):
    """Create repeatable NOMAD sections for all detected channels."""

    output = []

    for channel_data in channels:

        channel = SulfurizationChannel()

        channel.channel_id = channel_data["channel_id"]
        channel.name = channel_data["name"]
        channel.unit = channel_data["unit"]

        channel.values = np.asarray(
            channel_data["values"],
            dtype=float,
        )

        statistics = stability_results.get(
            channel_data["name"]
        )

        if statistics is not None:

            channel.mean = statistics["mean"]
            channel.std = statistics["std"]
            channel.minimum = statistics["minimum"]
            channel.maximum = statistics["maximum"]
            channel.range = statistics["range"]

        output.append(channel)

    return output


# ============================================================
# 6. Populate holding-period section
# ============================================================

def create_holding_section(holding_period):
    """Create the NOMAD holding-period subsection."""

    section = SulfurizationHoldingPeriod()

    section.hold_channel = HOLD_CHANNEL
    section.target_temperature_c = TARGET_TEMPERATURE
    section.temperature_tolerance_c = TEMPERATURE_TOLERANCE
    section.minimum_duration_s = MIN_HOLD_DURATION_S

    section.detected = holding_period is not None

    if holding_period is not None:

        section.start_index = holding_period["first"]
        section.end_index = holding_period["last"]

        section.start_time_s = holding_period["start_time_s"]
        section.end_time_s = holding_period["end_time_s"]

        section.duration_s = holding_period["duration_s"]

    return section


# ============================================================
# 7. Build the complete NOMAD entry
# ============================================================

def create_sulfurization_run(
    filename,
    metadata,
    time_data,
    channels,
):
    """Convert decoded PLW measurements into a NOMAD schema entry."""

    # Detect stable furnace-temperature interval.
    holding_period = detect_holding_period(
        time_data,
        channels,
    )

    # Calculate channel statistics only if a hold is detected.
    stability_results = {}

    if holding_period is not None:

        stability_results = calculate_stability(
            channels,
            holding_period["first"],
            holding_period["last"],
        )

    # Root section.
    run = SulfurizationRun()

    run.source_filename = Path(filename).name

    run.plw_version = metadata["version"]
    run.sample_number = metadata["sample_number"]

    run.number_of_channels = metadata["n_channels"]
    run.number_of_samples = metadata["n_samples"]

    run.sampling_interval = metadata["interval"]
    run.time_unit_code = metadata["time_units"]

    run.channel_ids = metadata["channel_ids"]

    run.time_s = np.asarray(
        time_data,
        dtype=float,
    )

    if len(time_data):
        run.recorded_duration_s = float(
            time_data[-1] - time_data[0]
        )

    # Holding-period information.
    run.holding_period = create_holding_section(
        holding_period
    )

    # All original channels and their stability statistics.
    run.channels = create_channel_sections(
        channels,
        stability_results,
    )

    # Generate Plotly visualization.
    run.plot()

    return run


# ============================================================
# 8. NOMAD parser
# ============================================================

class SulfurizationParser(MatchingParser):
    """Parser for PicoLog PLW sulfurization measurements."""

    def parse(
        self,
        mainfile,
        archive: EntryArchive,
        logger=None,
        child_archives=None,
    ):

        log = logger or logging.getLogger(__name__)

        log.info(
            "Reading PicoLog sulfurization file: %s",
            mainfile,
        )

        # Read original binary PLW data.
        metadata, time_data, channels = read_plw(
            mainfile
        )

        log.info(
            "PLW file contains %d channels and %d samples.",
            metadata["n_channels"],
            metadata["n_samples"],
        )

        # Build NOMAD schema.
        run = create_sulfurization_run(
            mainfile,
            metadata,
            time_data,
            channels,
        )

        archive.data = run

        if run.holding_period.detected:

            hold = run.holding_period

            log.info(
                "Stable interval detected: %.2f to %.2f min "
                "(duration %.2f min).",
                hold.start_time_s / 60.0,
                hold.end_time_s / 60.0,
                hold.duration_s / 60.0,
            )

        else:

            log.warning(
                "No continuous holding period of at least %.1f seconds "
                "was detected around %.1f °C.",
                MIN_HOLD_DURATION_S,
                TARGET_TEMPERATURE,
            )

        log.info(
            "Successfully parsed sulfurization run: %s",
            run.source_filename,
        )
