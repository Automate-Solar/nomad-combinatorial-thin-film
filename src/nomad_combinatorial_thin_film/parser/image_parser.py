import logging
from pathlib import Path
from typing import TYPE_CHECKING

from nomad.parsing.parser import MatchingParser

import nomad_combinatorial_thin_film.plugin.utils as plugin_utils
from nomad_combinatorial_thin_film.parser.utils import (
    find_image_folders,
    find_synthesis_json,
    parse_image_folder,
    parse_synthesis_json,
)
from nomad_combinatorial_thin_film.plugin.image_plugin import ImageDataset

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive

logger_module = logging.getLogger(__name__)


class DataRootParser(MatchingParser):
    """Parser for sample folders with synthesis conditions and image data."""

    def parse(
        self,
        mainfile: str,
        archive: 'EntryArchive',
        logger=None,
        child_archives=None,
    ) -> None:
        log = logger or logger_module

        if archive.data is not None:
            log.debug('Archive already has data, skipping parse')
            return

        data_root = Path(mainfile).parent
        log.info('Parsing image sample folder: %s', data_root)

        try:
            dataset = ImageDataset()
            dataset.name = f'Image Dataset from {data_root.name}'

            synthesis_json = find_synthesis_json(data_root)
            if synthesis_json:
                dataset.synthesis_conditions = parse_synthesis_json(synthesis_json, log)
                log.info('Parsed synthesis conditions from %s', synthesis_json.name)

            experiments = []
            for image_folder in find_image_folders(data_root):
                experiment = parse_image_folder(image_folder, data_root, log)
                if experiment:
                    experiments.append(experiment)

            if not experiments:
                log.warning('No image data folders found in %s', data_root)
                archive.data = dataset
                return

            dataset.measurements = experiments
            dataset.figures = plugin_utils.collect_image_dataset_figures(experiments)
            archive.data = dataset

            log.info(
                'Successfully created dataset with %d image measurements',
                len(experiments),
            )

        except Exception as exc:
            log.error('Error parsing image sample folder: %s', str(exc), exc_info=True)
