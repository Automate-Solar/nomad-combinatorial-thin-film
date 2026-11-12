
"""Parser for rapid thermal processing JSON log files."""

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from nomad.datamodel import EntryArchive
from nomad.parsing import MatchingParser

from nomad_combinatorial_thin_film.plugin.rtp import (
    RTPChannel,
    RTPProgramStep,
    RTPRun,
)

logger = logging.getLogger(__name__)


def parse_rtp_datetime(value, field_name):
    """Convert standard or instrument-formatted timestamps to datetimes."""
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value

    value = str(value).strip()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(
                value,
                "%Y-%m-%dT%H-%M-%SZ",
            ).replace(tzinfo=UTC)
        except ValueError as exc:
            raise ValueError(
                f"Invalid RTP {field_name} timestamp: {value!r}"
            ) from exc


def load_existing_rtp_run(archive, logger=None):
    """Return a copy of an already archived RTP run during reprocessing."""
    log = logger or logging.getLogger(__name__)
    metadata = archive.metadata
    entry_id = getattr(metadata, "entry_id", None)
    context = archive.m_context
    upload_files = getattr(context, "upload_files", None)

    if not entry_id:
        log.info("No entry id is available; parsing the RTP source file.")
        return None

    if upload_files is None:
        log.info("No upload archive is available; parsing the RTP source file.")
        return None

    try:
        with upload_files.read_archive(entry_id) as archive_reader:
            previous_archive_data = archive_reader[entry_id]
            if hasattr(previous_archive_data, "to_json"):
                previous_archive_dict = previous_archive_data.to_json()
            else:
                previous_archive_dict = dict(previous_archive_data)

            previous_data = previous_archive_dict.get("data", {})
    except KeyError:
        # There is no previous archive on the first processing pass.
        log.info("No previous RTP archive exists; parsing the source file.")
        return None

    if not isinstance(previous_data, dict) or not previous_data:
        log.info("The previous archive has no RTP data; parsing the source file.")
        return None

    try:
        for field_name in ("start_datetime", "end_datetime"):
            if field_name in previous_data:
                previous_data[field_name] = parse_rtp_datetime(
                    previous_data[field_name],
                    field_name,
                )
        existing_run = RTPRun.m_from_dict(previous_data, m_context=context)
    except (TypeError, ValueError, KeyError):
        log.warning(
            "Could not restore the previous RTP archive; parsing the source file.",
            exc_info=True,
        )
        return None

    return existing_run.m_copy(deep=True)


# ============================================================
# 1. JSON reader and validation
# ============================================================

def read_rtp_json(filename):
    """Read and validate an RTP JSON file."""

    with open(filename, encoding="utf-8") as file:
        data = json.load(file)

    required = [
        "sample_id",
        "run_id",
        "time_series_data",
        "setpoints",
    ]

    missing = [key for key in required if key not in data]

    if missing:
        raise ValueError(
            f"RTP JSON is missing required fields: {missing}"
        )

    if not isinstance(data["time_series_data"], dict):
        raise ValueError(
            "'time_series_data' must be a dictionary."
        )

    return data


# ============================================================
# 2. Decode and align time-series data
# ============================================================

def decode_time_series(time_series_data):
    """
    Convert indexed JSON dictionaries into aligned NumPy arrays.

    The JSON stores each channel as:
        channel_name: {
            "932": value,
            "933": value,
            ...
        }

    All channels are aligned using the original sample indices.
    Missing values are represented by NaN.
    """

    if "time_[s]" not in time_series_data:
        raise ValueError(
            "The RTP JSON does not contain the required 'time_[s]' channel."
        )

    time_dict = time_series_data["time_[s]"]

    if not isinstance(time_dict, dict) or not time_dict:
        raise ValueError(
            "The 'time_[s]' channel is empty or invalid."
        )

    try:
        sample_indices = sorted(
            time_dict.keys(),
            key=int,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Time-series sample indices must be integer-like strings."
        ) from exc

    time_s = np.asarray(
        [float(time_dict[index]) for index in sample_indices],
        dtype=float,
    )

    if not np.all(np.isfinite(time_s)):
        raise ValueError(
            "The time channel contains non-finite values."
        )

    if np.any(np.diff(time_s) < 0):
        raise ValueError(
            "The time channel is not monotonically increasing."
        )

    channels = []

    for channel_name, channel_dict in time_series_data.items():

        if channel_name == "time_[s]":
            continue

        if not isinstance(channel_dict, dict):
            logger.warning(
                "Skipping invalid channel %s: expected a dictionary.",
                channel_name,
            )
            continue

        values = []

        for index in sample_indices:

            value = channel_dict.get(index)

            if value is None:
                values.append(np.nan)
            else:
                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    values.append(np.nan)

        values = np.asarray(values, dtype=float)

        # Extract unit from channel name, e.g. temp_[C].
        match = re.search(r"_\[([^\]]+)\]$", channel_name)

        unit = match.group(1) if match else ""

        # Remove unit suffix for a readable display name.
        readable_name = re.sub(
            r"_\[[^\]]+\]$",
            "",
            channel_name,
        )

        readable_name = readable_name.replace("_", " ").title()

        channels.append(
            {
                "original_name": channel_name,
                "name": readable_name,
                "unit": unit,
                "values": values,
            }
        )

    return time_s, channels


# ============================================================
# 3. Build temperature program sections
# ============================================================

def create_program_steps(setpoints):
    """Convert RTP temperature steps into NOMAD subsections."""

    output = []

    steps = setpoints.get("rtp_steps", [])

    if not isinstance(steps, list):
        raise ValueError("'rtp_steps' must be a list.")

    for index, step_data in enumerate(steps, start=1):

        if not isinstance(step_data, dict):
            raise ValueError(
                f"RTP step {index} is not a valid dictionary."
            )

        step = RTPProgramStep()

        step.step_number = index

        step.target_temperature_c = step_data.get(
            "temperature_[C]"
        )

        step.ramp_rate_c_min = step_data.get(
            "ramp_rate_[C/min]"
        )

        step.dwell_time_min = step_data.get(
            "dwell_time_[min]"
        )

        output.append(step)

    return output


# ============================================================
# 4. Build channel sections
# ============================================================

def create_channel_sections(channel_data):
    """Create NOMAD measurement-channel subsections."""

    output = []

    for item in channel_data:

        channel = RTPChannel()

        channel.name = item["name"]
        channel.unit = item["unit"]

        values = np.asarray(
            item["values"],
            dtype=float,
        )

        channel.values = values

        finite_values = values[np.isfinite(values)]

        if len(finite_values):

            channel.mean = float(np.mean(finite_values))
            channel.minimum = float(np.min(finite_values))
            channel.maximum = float(np.max(finite_values))

        output.append(channel)

    return output


# ============================================================
# 5. Build complete RTP entry
# ============================================================

def create_rtp_run(filename, data):
    """Convert decoded RTP JSON data into a NOMAD RTPRun."""

    time_s, channel_data = decode_time_series(
        data["time_series_data"]
    )

    setpoints = data.get("setpoints", {})

    run = RTPRun()

    # --------------------------------------------------------
    # General metadata
    # --------------------------------------------------------

    run.sample_id = data.get("sample_id")
    run.run_id = data.get("run_id")

    run.source_filename = Path(filename).name

    run.start_datetime = parse_rtp_datetime(
        data.get("start_datetime"),
        "start_datetime",
    )
    run.end_datetime = parse_rtp_datetime(
        data.get("end_datetime"),
        "end_datetime",
    )

    run.start_temperature_c = data.get(
        "start_temperature_[C]"
    )

    run.base_pressure_hpa = data.get(
        "base_pressure_[hPa]"
    )

    # --------------------------------------------------------
    # Process settings
    # --------------------------------------------------------

    run.process_gas_pressure = setpoints.get(
        "process_gas_pressure"
    )

    run.forced_cooling = data.get(
        "forced_cooling"
    )

    run.final_cool_rate_c_min = setpoints.get(
        "final_cool_rate_[C/min]"
    )

    run.stop_temperature_c = setpoints.get(
        "stop_temperature_[C]"
    )

    # --------------------------------------------------------
    # Source paths
    # --------------------------------------------------------

    run.log_file = data.get("log_file")
    run.plot_file = data.get("plot_file")

    # --------------------------------------------------------
    # Time-series information
    # --------------------------------------------------------

    run.time_s = time_s

    run.number_of_samples = len(time_s)

    if len(time_s):
        run.duration_s = float(
            time_s[-1] - time_s[0]
        )

    # --------------------------------------------------------
    # Temperature program
    # --------------------------------------------------------

    run.temperature_steps = create_program_steps(
        setpoints
    )

    # --------------------------------------------------------
    # Measurement channels
    # --------------------------------------------------------

    run.channels = create_channel_sections(
        channel_data
    )

    # --------------------------------------------------------
    # Errors
    # --------------------------------------------------------

    errors = data.get("errors", [])

    run.errors = [
        str(error) if not isinstance(error, dict)
        else json.dumps(error)
        for error in errors
    ]

    # --------------------------------------------------------
    # Visualization
    # --------------------------------------------------------

    run.plot()

    return run


# ============================================================
# 6. NOMAD parser
# ============================================================

class RTPParser(MatchingParser):
    """Parser for rapid thermal processing JSON log files."""

    def parse(
        self,
        mainfile,
        archive: EntryArchive,
        logger=None,
        child_archives=None,
    ):

        log = logger or logging.getLogger(__name__)

        existing_run = load_existing_rtp_run(archive, logger=log)
        if existing_run is not None:
            existing_run.plot()
            archive.data = existing_run
            log.info(
                "Reusing the existing RTP data and preserving ELN edits; "
                "the input JSON was not reread."
            )
            return

        log.info(
            "Reading RTP JSON file: %s",
            mainfile,
        )

        # Read original JSON.
        data = read_rtp_json(mainfile)

        # Decode and populate NOMAD schema.
        run = create_rtp_run(
            mainfile,
            data,
        )

        if archive.metadata and archive.metadata.mainfile:
            run.source_filename = archive.metadata.mainfile

        archive.data = run

        log.info(
            "Successfully parsed RTP run %s for sample %s.",
            run.run_id,
            run.sample_id,
        )

        log.info(
            "RTP dataset contains %d samples and %d measurement channels.",
            run.number_of_samples,
            len(run.channels),
        )
