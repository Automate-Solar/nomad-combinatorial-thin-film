from typing import TYPE_CHECKING

from nomad.datamodel.data import ArchiveSection
from nomad.datamodel.metainfo.action import ActionSection
from nomad.datamodel.metainfo.annotations import ELNAnnotation, SectionProperties
from nomad.datamodel.metainfo.eln import ElnParserSection
from nomad.datamodel.metainfo.plot import PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

import nomad_combinatorial_thin_film.plugin.utils as plu
from nomad_combinatorial_thin_film.categories import Uppsala
from nomad_combinatorial_thin_film.plugin.eln_utils import (
    replace_section_data,
)

m_package = Package(
    name='hyperspectral_image_plugin',
    description='Schema for hyperspectral image datasets.',
    categories=[Uppsala],
)


# ============================================================
# Acquisition Metadata
# ============================================================


class AcquisitionMetadata(ArchiveSection):
    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'interleave',
                    'data_type',
                    'sample_binning',
                    'spectral_binning',
                    'line_binning',
                    'shutter',
                    'gain',
                    'framerate',
                    'temperature',
                    'imager_serial_number',
                    'rotation',
                    'pixel_size',
                    'byte_order',
                    'header_offset',
                    'flip_radiometric_calibration',
                    'reflection_scale_factor',
                    'wavelength_unit',
                    'label',
                    'history',
                ]
            )
        )
    )

    interleave = Quantity(
        type=str,
        description='BIL, BSQ or BIP',
        a_eln={
            'component': 'StringEditQuantity',
            'choices': ['bil', 'bsq', 'bip', 'BIL', 'BSQ', 'BIP'],
        },
    )

    data_type = Quantity(
        type=str,
        description='Data type stored in cube',
        a_eln={'component': 'StringEditQuantity'},
    )

    sample_binning = Quantity(
        type=int,
        description='Binning factor in the sample dimension.',
        a_eln={'component': 'NumberEditQuantity'},
    )
    spectral_binning = Quantity(
        type=int,
        description='Binning factor in the spectral dimension.',
        a_eln={'component': 'NumberEditQuantity'},
    )
    line_binning = Quantity(
        type=int,
        description='Binning factor in the line dimension.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    shutter = Quantity(
        type=float,
        description='Shutter value used during acquisition.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    gain = Quantity(
        type=float,
        description='Gain setting used during acquisition.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    framerate = Quantity(
        type=float,
        description='Frame rate of the hyperspectral image.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    temperature = Quantity(
        type=float,
        description='Temperature during acquisition.',
        a_eln={'component': 'NumberEditQuantity'},
    )
    imager_serial_number = Quantity(
        type=str,
        description='Serial number of the imager.',
        a_eln={'component': 'StringEditQuantity'},
    )

    rotation = Quantity(
        type=str,
        description='Rotation metadata of the hyperspectral image.',
        a_eln={'component': 'StringEditQuantity'},
    )

    pixel_size = Quantity(
        type=float,
        description='Size of each pixel in the hyperspectral image.',
        a_eln={'component': 'NumberEditQuantity'},
    )
    byte_order = Quantity(
        type=str,
        description='Byte order of the data.',
        a_eln={'component': 'StringEditQuantity'},
    )

    header_offset = Quantity(
        type=int,
        description='Offset of the header in the data file.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    flip_radiometric_calibration = Quantity(
        type=bool,
        description='Whether to flip the radiometric calibration data.',
        a_eln={'component': 'BoolEditQuantity'},
    )

    reflection_scale_factor = Quantity(
        type=float,
        description='Scale factor for reflection data.',
        a_eln={'component': 'NumberEditQuantity'},
    )
    wavelength_unit = Quantity(
        type=str,
        description='Unit for the wavelength values.',
        a_eln={'component': 'StringEditQuantity'},
    )
    label = Quantity(
        type=str,
        description='Label for the hyperspectral image.',
        a_eln={'component': 'StringEditQuantity'},
    )
    history = Quantity(
        type=str,
        description='History of the hyperspectral image.',
        a_eln={'component': 'StringEditQuantity'},
    )


# ============================================================
# Cube Metadata
# ============================================================


class CubeMetadata(ArchiveSection):
    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'lines',
                    'samples',
                    'bands',
                    'wavelength',
                    'wavelength_min_nm',
                    'wavelength_max_nm',
                    'interleave',
                    'data_type',
                ]
            )
        )
    )

    lines = Quantity(
        type=int,
        description='Number of spatial scan lines.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    samples = Quantity(
        type=int,
        description='Number of spatial samples.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    bands = Quantity(
        type=int,
        description='Number of spectral bands.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    wavelength = Quantity(
        type=float,
        shape=['*'],
        unit='nanometer',
        description='Wavelength values corresponding to each spectral band.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    wavelength_min_nm = Quantity(
        type=float,
        unit='nanometer',
        description='Minimum wavelength.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    wavelength_max_nm = Quantity(
        type=float,
        unit='nanometer',
        description='Maximum wavelength.',
        a_eln={'component': 'NumberEditQuantity'},
    )

    interleave = Quantity(
        type=str,
        description='BIL, BSQ or BIP.',
        a_eln={
            'component': 'StringEditQuantity',
            'choices': ['bil', 'bsq', 'bip', 'BIL', 'BSQ', 'BIP'],
        },
    )

    data_type = Quantity(
        type=str,
        description='Underlying storage datatype.',
        a_eln={'component': 'StringEditQuantity'},
    )


# ============================================================
# Raw Data Files
# ============================================================


class HyperspectralRawData(ArchiveSection):
    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'hdr_file',
                    'bil_file',
                    'cube_npy',
                    'rgb_preview',
                ]
            )
        )
    )

    hdr_file = Quantity(
        type=str,
        a_eln={'component': 'FileEditQuantity'},
    )

    bil_file = Quantity(
        type=str,
        a_eln={'component': 'FileEditQuantity'},
    )

    cube_npy = Quantity(
        type=str,
        a_eln={'component': 'FileEditQuantity'},
    )

    rgb_preview = Quantity(
        type=str,
        a_eln={'component': 'FileEditQuantity'},
    )


# ============================================================
# Visualization Section
# ============================================================
class HyperspectralAnalysis(
    PlotSection,
    ArchiveSection,
):
    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        super().normalize(archive, logger)

    def create_analysis_figures(self, cube_path, hdr_path, logger=None):
        self.figures = plu.create_hyperspectral_overview_figures(
            cube_path,
            hdr_path,
            logger,
        )


# ============================================================
# Measurement
# ============================================================


class HyperspectralMeasurement(ArchiveSection):
    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'acquisition_metadata',
                    'cube_metadata',
                    'raw_data',
                    'visualization',
                    'label',
                    'history',
                ]
            )
        )
    )

    acquisition_metadata = SubSection(
        section_def=AcquisitionMetadata,
    )

    cube_metadata = SubSection(
        section_def=CubeMetadata,
    )

    raw_data = SubSection(
        section_def=HyperspectralRawData,
    )

    visualization = SubSection(
        section_def=HyperspectralAnalysis,
    )

    label = Quantity(
        type=str,
        a_eln={'component': 'StringEditQuantity'},
    )

    history = Quantity(
        type=str,
        a_eln={'component': 'StringEditQuantity'},
    )

    def normalize(
        self,
        archive,
        logger,
    ):

        super().normalize(
            archive,
            logger,
        )

        if not self.visualization:
            return

        # visualization = self.visualization


# ============================================================
# Dataset
# ============================================================


class HyperspectralReloadAction(ActionSection):
    """Button for explicitly reloading source-derived hyperspectral data."""

    action_trigger = Quantity(
        type=bool,
        description='Replace parsed values with values from the uploaded ENVI files.',
        a_eln={
            'component': 'ActionEditQuantity',
            'label': 'Reload from source',
        },
    )

    def perform_action(self, archive, logger):
        self.m_parent.reload_from_source(archive, logger)


class HyperspectralDataset(PlotSection, ElnParserSection):
    m_def = Section(
        categories=[Uppsala],
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'data_file',
                    'name',
                    'user_notes',
                    'reload_action',
                    'measurements',
                ]
            )
        ),
    )

    name = Quantity(
        type=str,
        a_eln={'component': 'StringEditQuantity'},
    )

    data_file = Quantity(
        type=str,
        description='Uploaded ENVI header file used to populate this dataset.',
        a_eln={'component': 'FileEditQuantity'},
    )

    user_notes = Quantity(
        type=str,
        description='User notes preserved when source data is reloaded.',
        a_eln={'component': 'RichTextEditQuantity'},
    )

    source_loaded = Quantity(
        type=bool,
        description='Internal flag indicating that source data was loaded.',
    )

    reload_action = SubSection(section_def=HyperspectralReloadAction)

    measurements = SubSection(
        section_def=HyperspectralMeasurement,
        repeats=True,
    )

    def normalize(
        self,
        archive,
        logger,
    ):
        if self.reload_action is None:
            self.reload_action = HyperspectralReloadAction()

        super().normalize(
            archive,
            logger,
        )

        if not self.source_loaded:
            self.reload_from_source(archive, logger)
        else:
            self.refresh_plots(archive, logger)

    def reload_from_source(self, archive, logger):
        """Replace source-derived data and figures from the ENVI files."""
        if not self.data_file:
            logger.warning('No source ENVI file is assigned; cannot reload data.')
            return

        from nomad_combinatorial_thin_film.parser.hyperspectral_parser import (
            build_hyperspectral_dataset,
        )

        parsed_dataset = build_hyperspectral_dataset(
            self.data_file,
            logger,
            context=archive.m_context,
        )
        if parsed_dataset is None:
            return

        replace_section_data(
            self,
            parsed_dataset,
            preserved_names={
                'data_file',
                'source_loaded',
                'user_notes',
                'reload_action',
            },
        )
        self.source_loaded = True
        self.refresh_plots(archive, logger)

    def refresh_plots(self, archive, logger):
        """Regenerate measurement and dataset plots from the current files."""
        import numpy as np

        from nomad_combinatorial_thin_film.parser.utils import (
            collect_dataset_figures,
            extract_wavelengths,
            read_envi_hdr,
        )

        for measurement in self.measurements:
            if measurement.raw_data is None or measurement.visualization is None:
                continue

            with archive.m_context.raw_file(
                measurement.raw_data.cube_npy,
                'rb',
            ) as cube_file:
                cube = np.load(cube_file)
            with archive.m_context.raw_file(
                measurement.raw_data.hdr_file,
                'rt',
            ) as hdr_file:
                hdr = read_envi_hdr(hdr_file)
            wavelengths = extract_wavelengths(hdr)
            measurement.visualization.figures = (
                plu.create_hyperspectral_overview_figures(
                    cube,
                    wavelengths,
                    logger,
                )
            )

        self.figures = collect_dataset_figures(self.measurements)


m_package.__init_metainfo__()
