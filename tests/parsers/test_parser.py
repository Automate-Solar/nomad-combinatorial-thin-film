import json
import logging
from pathlib import Path

from nomad.datamodel import EntryArchive

from plugin_img.parser.image_parser import DataRootParser

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


def _parse_sample(sample_root: Path) -> EntryArchive:
    parser = DataRootParser()
    archive = EntryArchive()
    marker_file = sample_root / 'nomad_collect.txt'
    marker_file.touch(exist_ok=True)
    parser.parse(str(marker_file), archive, logging.getLogger())
    return archive


def test_parse_image_sample_folder_creates_dataset_entry():
    sample_root = DATA_DIR / 'data-img'
    archive = _parse_sample(sample_root)

    assert archive.data is not None
    assert archive.data.name.startswith('Image Dataset from')

    measurements = getattr(archive.data, 'measurements', None)
    assert measurements is not None
    assert len(measurements) >= 1

    assert any(
        getattr(measurement, 'image_preview', None)
        or getattr(measurement.image, 'image_preview', None)
        for measurement in measurements
    )

    for measurement in measurements:
        assert measurement.timestamp
        assert measurement.name
        assert measurement.image is not None or measurement.manifest_data is not None


def test_parse_without_image_files_creates_dataset_entry_with_synthesis_conditions(
    tmp_path,
):
    sample_root = tmp_path / 'sample-image-root'
    sample_root.mkdir()
    json_file = sample_root / 'synthesis.json'
    json_file.write_text(json.dumps({'date': '2026-06-05', 'cu_source_power': 42}))

    archive = _parse_sample(sample_root)
    assert archive.data is not None
    assert archive.data.name.startswith('Image Dataset from')
    assert getattr(archive.data, 'measurements', None) in (None, [])
    assert archive.data.synthesis_conditions is not None
    assert archive.data.synthesis_conditions.Date == '2026-06-05'

