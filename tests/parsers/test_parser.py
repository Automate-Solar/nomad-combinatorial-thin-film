import logging
from pathlib import Path

from nomad.datamodel import EntryArchive

from nomad_combinatorial_thin_film.parser.image_parser import DataRootParser

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'


def _parse_sample(sample_root: Path) -> EntryArchive:
    parser = DataRootParser()
    archive = EntryArchive()
    marker_file = sample_root / 'nomad_collect.txt'
    marker_file.touch(exist_ok=True)
    parser.parse(str(marker_file), archive, logging.getLogger())
    return archive
