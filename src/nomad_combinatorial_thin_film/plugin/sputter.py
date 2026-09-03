import json
import time
from datetime import datetime
from typing import TYPE_CHECKING, Self

import numpy as np
import pandas as pd

from nomad_combinatorial_thin_film.categories import (
    Uppsala
)
from nomad.datamodel.data import ArchiveSection, Schema
from nomad.datamodel.metainfo.annotations import (
    BrowserAdaptors,
    BrowserAnnotation,
    ELNAnnotation,
    ELNComponentEnum,
    Filter,
    SectionProperties,
)

from nomad.datamodel.metainfo.basesections import (
    Component,
    CompositeSystem,
    CompositeSystemReference,
    ElementalComposition,
    InstrumentReference,
    PureSubstanceComponent,
    PureSubstanceSection,
)
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.datamodel.metainfo.workflow import Link
from nomad.datamodel.results import Material, Results
from nomad.metainfo import MEnum, MProxy, Package, Quantity, Section, SubSection
from nomad.units import ureg
from nomad_material_processing.general import (
    SubstrateReference,
    ThinFilm,
    ThinFilmReference,
)
from nomad_material_processing.vapor_deposition.general import (
    ChamberEnvironment,
    GasFlow,
    Pressure,
    SubstrateHeater,
    TimeSeries,
    VolumetricFlowRate,
)
from nomad_material_processing.vapor_deposition.pvd.general import (
    PVDEvaporationSource,
    PVDSource,
    PVDStep,
)
from nomad_material_processing.vapor_deposition.pvd.sputtering import SputterDeposition
from nomad_measurements.utils import create_archive, merge_sections


from nomad_dtu_nanolab_plugin.schema_packages.gas import DTUGasSupply
from nomad_dtu_nanolab_plugin.schema_packages.sample import (
    DTUCombinatorialLibrary,
    ProcessParameterOverview,
)
from nomad_dtu_nanolab_plugin.schema_packages.substrate import (
    DTUSubstrate,
    DTUSubstrateBatch,
)
from nomad_dtu_nanolab_plugin.schema_packages.target import DTUTarget


if TYPE_CHECKING:
    from nomad.datamodel.datamodel import EntryArchive
    from structlog.stdlib import BoundLogger

    from nomad_dtu_nanolab_plugin.schema_packages import SputteringEntryPoint

import os

from nomad.config import config

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
                visible=Filter(exclude=[
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

