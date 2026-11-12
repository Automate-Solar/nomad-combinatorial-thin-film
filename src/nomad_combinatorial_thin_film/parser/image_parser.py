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


def build_image_dataset(
    data_root: Path,
    log,
    upload_root: Path | None = None,
) -> ImageDataset | None:
    """Build an image dataset from a sample folder."""
    try:
        dataset = ImageDataset()
        dataset.name = f'Image Dataset from {data_root.name}'

        synthesis_json = find_synthesis_json(data_root)
        if synthesis_json:
            dataset.synthesis_conditions = parse_synthesis_json(synthesis_json, log)
            log.info('Parsed synthesis conditions from %s', synthesis_json.name)

        experiments = []
        for image_folder in find_image_folders(data_root):
            experiment = parse_image_folder(
                image_folder,
                data_root,
                log,
                upload_root=upload_root,
            )
            if experiment:
                experiments.append(experiment)

        dataset.measurements = experiments
        dataset.figures = plugin_utils.collect_image_dataset_figures(experiments)
        return dataset
    except Exception:
        log.error('Error parsing image sample folder: %s', data_root, exc_info=True)
        return None


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
        data_root = Path(mainfile).parent
        log.info('Parsing image sample folder: %s', data_root)
        dataset = build_image_dataset(data_root, log)
        if dataset is None:
            return
        archive.data = dataset
        if not dataset.measurements:
            log.warning('No image data folders found in %s', data_root)
        else:
            log.info(
                'Successfully created dataset with %d image measurements',
                len(dataset.measurements),
            )
