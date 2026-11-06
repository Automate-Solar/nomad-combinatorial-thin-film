import re
import zipfile

from nomad_combinatorial_thin_film.parser import xrd_parser_entry_point
from nomad_combinatorial_thin_film.parser.xrd_parser import (
    create_xrd_run,
    load_xrd_files,
)

EXPECTED_PATTERN_COUNT = 10


def test_xrd_zip_creates_one_run_with_all_patterns(tmp_path):
    archive_path = tmp_path / "CuZn10min.xrdzip"
    positions = [
        "phi0(0,-15)",
        "phi0(0,-7)",
        "phi0(0,0)",
        "phi0(0,7)",
        "phi0(0,15)",
        "phi90(-15,0)",
        "phi90(-7,0)",
        "phi90(0,0)",
        "phi90(7,0)",
        "phi90(15,0)",
    ]
    xrdml = b"""<?xml version="1.0"?>
    <xrdMeasurements><scan><dataPoints>
      <positions axis="2Theta"><startPosition>10</startPosition>
        <endPosition>14</endPosition></positions>
      <intensities>1 5 10 5 1</intensities>
    </dataPoints></scan></xrdMeasurements>"""

    with zipfile.ZipFile(archive_path, "w") as archive:
        for index, position in enumerate(positions):
            archive.writestr(f"CuZn10min_{index} {position}.xrdml", xrdml)

    records, input_format = load_xrd_files(archive_path)
    run = create_xrd_run(archive_path, records, input_format)

    assert len(run.patterns) == EXPECTED_PATTERN_COUNT
    assert run.number_of_patterns == EXPECTED_PATTERN_COUNT
    assert run.name == "CuZn10min"
    assert len(run.figures) == 1
    assert re.fullmatch(xrd_parser_entry_point.mainfile_name_re, "CuZn10min.zip")
    assert re.fullmatch(xrd_parser_entry_point.mainfile_name_re, archive_path.name)
    assert not re.fullmatch(
        xrd_parser_entry_point.mainfile_name_re,
        "CuZn10min phi90(7,0).xrdml",
    )
