import logging
from pathlib import Path
from typing import TYPE_CHECKING

from nomad.parsing.parser import MatchingParser

from nomad_combinatorial_thin_film.parser.utils import (
    collect_dataset_figures,
    find_hyperspectral_folders,
    parse_hyperspectral_folder,
)
from nomad_combinatorial_thin_film.plugin.hyperspectral_plugin import (
    HyperspectralDataset,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive

logger_module = logging.getLogger(__name__)


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

        if archive.data is not None:
            return

        root = Path(mainfile).parent

        dataset = HyperspectralDataset()
        dataset.name = f'Hyperspectral Dataset - {root.name}'

        measurements = []
        for folder in find_hyperspectral_folders(root):
            measurement = parse_hyperspectral_folder(folder, root, log)
            if measurement:
                measurements.append(measurement)

        dataset.measurements = measurements
        dataset.figures = collect_dataset_figures(measurements)
        archive.data = dataset

        log.info('Parsed %d hyperspectral measurements', len(measurements))
