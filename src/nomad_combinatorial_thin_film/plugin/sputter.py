from typing import TYPE_CHECKING

from nomad.datamodel.data import ArchiveSection, Schema
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    ELNComponentEnum,
    Filter,
    SectionProperties,
)
from nomad.datamodel.metainfo.basesections import (
    InstrumentReference,
)
from nomad.datamodel.metainfo.plot import PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection

from nomad_combinatorial_thin_film.categories import Uppsala

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

from nomad_dtu_nanolab_plugin.schema_packages.sputtering import (
    DTUSputtering,
)

m_package = Package()


class UppsalaSputteringInstruments(InstrumentReference, ArchiveSection):
    m_def = Section()

    system_status_number = Quantity(
        type=int,
        description='The system status number of the instrument.',
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    # This class should come with a field for an instrument reference and a name
    # As you told me the syastem has a status number I implemented that here.
    # Add any other quantities here that you think are relevant for the instrument reference
    # or change it to contain all instrument information directly (suggest changing the type then)
    # add processing functions here below and adjust the normalize function
    # for now it just fetches the name of the instrument if there is a reference
    # any thing in the normalize function triggeres EVERY time you press save on the gui
    # keep that in mind for heavy calculations. You can avoid triggering reparsing for example
    # by checking if a certain quantiy is filled or boolean is set to true before starting the
    # parsing of the files

    def normalize(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:
        """
        The normalizer for the `InstrumentParameters` class.

        Args:
            archive (EntryArchive): The archive containing the section that is being
            normalized.
            logger (BoundLogger): A structlog logger.
        """
        super().normalize(archive, logger)
        if self.reference is not None:
            self.lab_id = self.reference.lab_id
            self.name = self.reference.name


class UppsalaSputtering(DTUSputtering, PlotSection, Schema):
    m_def = Section(
        categories=[Uppsala],
        label='Sputtering',
        links=['http://purl.obolibrary.org/obo/CHMO_0001328'],
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'lab_id',
                    'log_file',
                    'base_pressure',
                    'location',
                    'process_logfile',
                    'overwrite',
                    'deposition_parameters',
                    'substrates',
                    'samples',
                    'steps',
                    'source_ramp_up',
                    'source_presput',
                    'source_deprate',
                    'instruments',
                    'flags',
                ],
                visible=Filter(
                    exclude=[
                        'sulfur_partial_pressure',
                        'end_of_process',
                        'sulfur_cracker_pressure',
                        'cracker_warmup_log_file',
                        'target_image_before',
                        'target_image_after',
                        'plasma_image',
                        'sample_image',
                        'optix_spectra',
                        'rga_file',
                        'temperature_ramp_up',
                        'temperature_ramp_down',
                        'optix_power_type',
                        'optix_current',
                        'platen_used',
                    ]
                ),
            ),
        ),
    )
    instruments = SubSection(
        section_def=UppsalaSputteringInstruments,
        repeats=False,
    )
    # this subsection exists in DTU sputtering, by reassigning it with
    # the same name you can overwrite e the definition and cutomize the subsection
    # this work similar for quantities
    # I defined a very small reference class to an instrument above.
    # To be able to use the diefinition the subsection class has to be defined before the class
    # Hope you find this and it helps :D


m_package.__init_metainfo__()
