from typing import TYPE_CHECKING

from nomad.datamodel.data import Schema
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    Filter,
    SectionProperties,
)
from nomad.datamodel.metainfo.plot import PlotSection
from nomad.metainfo import Package, Section

from nomad_combinatorial_thin_film.categories import Uppsala

if TYPE_CHECKING:
    pass


from nomad_dtu_nanolab_plugin.schema_packages.sputtering import (
    DTUSputtering,
)

m_package = Package()


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
                    'steps',
                    'temperature_ramp_up',
                    'source_ramp_up',
                    'source_presput',
                    'source_deprate',
                    'temperature_ramp_down',
                    'instrument',
                    'end_of_process',
                    'flags',
                ],
                visible=Filter(
                    exclude=[
                        'sulfur_partial_pressure',
                        'sulfur_cracker_pressure',
                        'cracker_warmup_log_file',
                        'target_image_before',
                        'target_image_after',
                        'plasma_image',
                        'sample_image',
                        'optix_spectra',
                        'rga_file',
                        'optix_power_type',
                        'optix_current',
                    ]
                ),
            ),
        ),
    )


m_package.__init_metainfo__()
