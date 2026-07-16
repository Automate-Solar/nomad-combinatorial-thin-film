#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from typing import TYPE_CHECKING

from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import ELNAnnotation, SectionProperties
from nomad.datamodel.metainfo.plot import PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection

import nomad_combinatorial_thin_film.plugin.utils as plu

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

m_package = Package(
    name='Image Analysis Schema',
    description='Schema for storing image analysis results and metadata in NOMAD.',
)


class BoundingBox(ArchiveSection):
    """
    Bounding box definition for the region of interest.
    Represents the rectangular boundaries of a circular ROI.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'x_min',
                    'y_min',
                    'x_max',
                    'y_max',
                    'width',
                    'height',
                ],
            ),
        ),
    )

    x_min = Quantity(
        type=int,
        description='Minimum X coordinate (left edge) in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    y_min = Quantity(
        type=int,
        description='Minimum Y coordinate (top edge) in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    x_max = Quantity(
        type=int,
        description='Maximum X coordinate (right edge) in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    y_max = Quantity(
        type=int,
        description='Maximum Y coordinate (bottom edge) in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    width = Quantity(
        type=int,
        description='Width of bounding box in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    height = Quantity(
        type=int,
        description='Height of bounding box in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the bounding box."""
        super().normalize(archive, logger)


class RegionOfInterest(ArchiveSection):
    """
    Circular region of interest (ROI) information.
    Defines the area of interest in the image with center, radius, and bounding box.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'center_x_px',
                    'center_y_px',
                    'radius_px',
                    'square_crop_size_px',
                    'bounding_box',
                ],
            ),
        ),
    )

    center_x_px = Quantity(
        type=float,
        description='X coordinate of circle center in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    center_y_px = Quantity(
        type=float,
        description='Y coordinate of circle center in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    radius_px = Quantity(
        type=float,
        description='Radius of the circular ROI in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    square_crop_size_px = Quantity(
        type=int,
        description='Size of the square crop around the circle in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    bounding_box = SubSection(
        section_def=BoundingBox,
        description='Bounding box coordinates for the ROI',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the region of interest."""
        super().normalize(archive, logger)


class ImageDimensions(ArchiveSection):
    """
    Image dimension and shape information.
    Contains the resolution, number of color channels, and pixel value range.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'height',
                    'width',
                    'channels',
                    'bit_depth',
                    'is_color',
                    'pixel_value_min',
                    'pixel_value_max',
                ],
            ),
        ),
    )

    height = Quantity(
        type=int,
        description='Image height (number of rows) in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    width = Quantity(
        type=int,
        description='Image width (number of columns) in pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    channels = Quantity(
        type=int,
        description='Number of color channels (e.g., 3 for RGB)',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    bit_depth = Quantity(
        type=int,
        description='Bit depth of the image pixels',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    is_color = Quantity(
        type=bool,
        description='Whether the image is color (True) or grayscale (False)',
        a_eln={
            'component': 'BoolEditQuantity',
        },
    )

    pixel_value_min = Quantity(
        type=int,
        description='Minimum pixel value in the image',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    pixel_value_max = Quantity(
        type=int,
        description='Maximum pixel value in the image',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the image dimensions."""
        super().normalize(archive, logger)


class ImageMetadata(ArchiveSection):
    """
    Acquisition settings and metadata for the image.
    Contains camera settings like exposure time, gain, and bit depth.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'timestamp',
                    'shape',
                    'exposure_ms',
                    'gain',
                    'bit_depth',
                    'is_color',
                    'min',
                    'max',
                ],
            ),
        ),
    )

    timestamp = Quantity(
        type=str,
        description='Timestamp when the image was acquired (ISO format or custom format)',
        a_eln={
            'component': 'StringEditQuantity',
        },
    )

    shape = Quantity(
        type=int,
        shape=['*'],
        description='Shape of the image array (e.g., [height, width, channels])',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    exposure_ms = Quantity(
        type=float,
        description='Exposure time in milliseconds',
        a_eln={
            'component': 'NumberEditQuantity',
            'defaultDisplayUnit': 'millisecond',
        },
        unit='millisecond',
    )

    gain = Quantity(
        type=float,
        description='Camera gain setting (typically 0-100)',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    bit_depth = Quantity(
        type=int,
        description='Bit depth of the image (e.g., 8-bit, 12-bit)',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    is_color = Quantity(
        type=bool,
        description='Whether the image is color (True) or grayscale (False)',
        a_eln={
            'component': 'BoolEditQuantity',
        },
    )

    min = Quantity(
        type=float,
        description='Minimum pixel value in the image',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    max = Quantity(
        type=float,
        description='Maximum pixel value in the image',
        a_eln={
            'component': 'NumberEditQuantity',
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the image metadata."""
        super().normalize(archive, logger)


class ManifestData(ArchiveSection):
    """
    Experiment parameters and conditions from manifest.csv file.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'Date',
                    'Cu_source_power',
                    'Sn_source_power',
                    'Zn_source_power',
                    'Pressure',
                    'Source_temperature',
                    'Process_temperature',
                ],
            ),
        ),
    )

    Date = Quantity(
        type=str,
        description='Date of the measurement',
        a_eln={'component': 'StringEditQuantity'},
    )

    Cu_source_power = Quantity(
        type=float,
        unit='watt',
        description='Cu source power',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Sn_source_power = Quantity(
        type=float,
        unit='watt',
        description='Sn source power',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Zn_source_power = Quantity(
        type=float,
        unit='watt',
        description='Zn source power',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Pressure = Quantity(
        type=float,
        unit='pascal',
        description='Chamber pressure',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Source_temperature = Quantity(
        type=float,
        unit='kelvin',
        description='Source temperature',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Process_temperature = Quantity(
        type=float,
        unit='kelvin',
        description='Process temperature',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Chamber_pressure = Quantity(
        type=float,
        unit='pascal',
        description='Chamber pressure during process',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Process_time = Quantity(
        type=float,
        unit='second',
        description='Process time',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Cooling_time = Quantity(
        type=float,
        unit='second',
        description='Cooling time',
        a_eln={'component': 'NumberEditQuantity'},
    )

    Cooling_rate = Quantity(
        type=float,
        unit='kelvin / second',
        description='Cooling rate',
        a_eln={'component': 'NumberEditQuantity'},
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize manifest data."""
        super().normalize(archive, logger)


class ImageVisualization(ArchiveSection):
    """
    Image visualization section containing PNG preview for display.
    Stores the converted image file for viewing in the GUI.
    The image_file path will be rendered as an image in NOMAD's ELN interface.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'image_file',
                ],
            ),
        ),
    )

    image_file = Quantity(
        type=str,
        description='Path to the PNG preview image file. NOMAD will render this as an image in the GUI.',
        a_eln={
            'component': 'FileEditQuantity',
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize image visualization."""
        super().normalize(archive, logger)


class ImageData(PlotSection, ArchiveSection):
    """
    Image data and dimensions information.
    Links to image file and contains dimension metadata.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'dimensions',
                    'roi',
                    'visualization',
                    'image_array',
                    'image_preview',
                ],
            ),
        ),
    )

    dimensions = SubSection(
        section_def=ImageDimensions,
        description='Image dimensions and shape.',
    )

    roi = SubSection(
        section_def=RegionOfInterest,
        description='Region of interest information.',
    )

    visualization = SubSection(
        section_def=ImageVisualization,
        description='Image visualization with PNG preview file.',
    )

    image_array = Quantity(
        type=str,
        description='Path to the raw image data file (NPY format).',
        a_eln={
            'component': 'FileEditQuantity',
        },
    )

    image_preview = Quantity(
        type=str,
        description='Path to a PNG preview image generated from the raw image data for visualization.',
        a_eln={
            'component': 'FileEditQuantity',
        },
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize image data."""

        super().normalize(archive, logger)

        if self.image_array:
            try:
                image_path = archive.m_context.raw_file(str(self.image_array))

                self.create_image_plot(
                    image_path,
                    logger,
                )

            except Exception as exc:
                logger.warning(f'Could not generate image plot: {exc}')

    def create_image_plot(self, npy_path, logger=None) -> None:
        """Create an in-NOMAD Plotly image visualization from the NPY data."""
        self.figures = plu.create_image_plot(
            npy_path,
            roi=self.roi,
            logger=logger,
        )


class ImageExperimentRun(ArchiveSection):
    """
    Represents one image acquisition experiment measurement.
    Contains timestamp, experiment conditions (manifest data), metadata, and image data.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'timestamp',
                    'name',
                    #'manifest_data',
                    'metadata',
                    'image',
                ]
            )
        ),
    )

    timestamp = Quantity(
        type=str,
        description='Timestamp/folder name of the measurement (e.g., 20260323_133255).',
        a_eln={'component': 'StringEditQuantity'},
    )

    name = Quantity(
        type=str,
        description='A descriptive name for the experiment run.',
        a_eln={'component': 'StringEditQuantity'},
    )

    manifest_data = SubSection(
        section_def=ManifestData,
        description='Experiment parameters from manifest file.',
    )

    metadata = SubSection(
        section_def=ImageMetadata,
        description='Image acquisition metadata.',
    )

    image = SubSection(
        section_def=ImageData,
        description='Image data and dimensions.',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the experiment run."""
        super().normalize(archive, logger)


class ImageDataset(PlotSection, EntryData):
    """
    Represents a collection of image experiment measurements.
    Contains multiple ImageExperimentRun entries as subsections.
    """

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'name',
                    'synthesis_conditions',
                    'measurements',
                ]
            )
        ),
    )

    name = Quantity(
        type=str,
        description='A descriptive name for the dataset.',
        a_eln={'component': 'StringEditQuantity'},
    )

    measurements = SubSection(
        section_def=ImageExperimentRun,
        description='Collection of image experiment measurements.',
        repeats=True,
    )

    synthesis_conditions = SubSection(
        section_def=ManifestData,
        description='Sample-level synthesis conditions parsed from the root JSON file.',
    )

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """Normalize the dataset."""
        super().normalize(archive, logger)

        try:
            if not getattr(self, 'figures', None):
                self.figures = plu.collect_image_dataset_figures(self.measurements)
        except Exception as exc:
            logger.warning('Could not set dataset figures: %s', exc)


m_package.__init_metainfo__()


