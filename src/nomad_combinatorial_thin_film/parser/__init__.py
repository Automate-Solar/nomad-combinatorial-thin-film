from nomad.config.models.plugins import ElnParserEntryPoint, ParserEntryPoint


class PortableElnParserEntryPoint(ElnParserEntryPoint):
    """ELN parser entry point that normalizes source paths on Windows."""

    def load(self):
        from nomad_combinatorial_thin_film.parser.eln_parser import (
            ArchiveAwareElnMatchingParser,
        )

        return ArchiveAwareElnMatchingParser(**self.model_dump())


image_parser_entry_point = PortableElnParserEntryPoint(
    name='ImageParser',
    description='Parser for image datasets with metadata, ROI, and dimensions.',
    mainfile_name_re=r'(?i).*(?:synthesis\.json|\.(?:zip|imagezip))$',
    eln_m_def=('nomad_combinatorial_thin_film.plugin.image_plugin.ImageDataset'),
    data_type='RGB image dataset',
)


hyperspectral_parser_entry_point = PortableElnParserEntryPoint(
    name='HyperspectralParser',
    description=(
        'Parser for hyperspectral ENVI datasets with .hdr/.bil files or '
        '.zip/.hyperzip archives.'
    ),
    mainfile_name_re=r'(?i).*(?:\.hdr|\.(?:zip|hyperzip))$',
    eln_m_def=(
        'nomad_combinatorial_thin_film.plugin.hyperspectral_plugin.HyperspectralDataset'
    ),
    data_type='Hyperspectral ENVI dataset',
)


parser_entry_point = image_parser_entry_point


class ExperimentPlanParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.experiment_plan_parser import (
            ExperimentPlanParser,
        )

        return ExperimentPlanParser(**self.dict())


experiment_plan_parser_entry_point = ExperimentPlanParserEntryPoint(
    name='SputteringExperimentPlanParser',
    description=(
        'Parser for experiment_plan.txt files, including .zip, .planzip, '
        '.experimentzip, and .experimentplanzip archives.'
    ),
    mainfile_name_re=(
        r'(?i)(?:^|.*[/\\])experiment_plan\.txt$|'
        r'.*\.(?:zip|planzip|experimentzip|experimentplanzip)$'
    ),
)


sulfurization_parser_entry_point = PortableElnParserEntryPoint(
    name='SulfurizationParser',
    description=(
        'Parser for PicoLog PLW sulfurization temperature measurements, '
        'including .zip, .sulferzip, .sulfurzip, and .sulfurizationzip archives.'
    ),
    mainfile_name_re=(
        r'(?i).*(?:\.plw|\.(?:zip|sulferzip|sulfurzip|sulfurizationzip))$'
    ),
    eln_m_def=('nomad_combinatorial_thin_film.plugin.sulfurization.SulfurizationRun'),
    data_type='Sulfurization measurement',
)


class XRDParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.xrd_parser import (
            XRDParser,
        )

        return XRDParser(**self.dict())


xrd_parser_entry_point = XRDParserEntryPoint(
    name='XRDParser',
    description=(
        'Parser for spatially resolved XRD measurements '
        'from ZIP archives containing ASC or XRDML files. Use .xrdzip when '
        'uploading through a service that automatically extracts .zip files.'
    ),
    mainfile_name_re=r'(?i)^.*\.(?:zip|xrdzip)$',
)


class RTPParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.rtp_parser import RTPParser

        return RTPParser(**self.dict())


rtp_parser_entry_point = RTPParserEntryPoint(
    name='RTPParser',
    description=(
        'Parser for rapid thermal processing JSON files '
        'or .zip/.rtpzip archives containing process metadata and time-series measurements.'
    ),
    mainfile_name_re=r'(?i).*\.(?:json|zip|rtpzip)$',
    mainfile_contents_re=r'"run_id"\s*:',
)
