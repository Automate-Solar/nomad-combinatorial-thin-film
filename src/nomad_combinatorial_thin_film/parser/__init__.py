from nomad.config.models.plugins import ParserEntryPoint


class ImageParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.image_parser import DataRootParser

        return DataRootParser(**self.dict())


class HyperspectralParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.hyperspectral_parser import (
            HyperspectralRootParser,
        )

        return HyperspectralRootParser(**self.dict())


image_parser_entry_point = ImageParserEntryPoint(
    name='ImageParser',
    description='Parser for image datasets with metadata, ROI, and dimensions.',
    mainfile_name_re=r'.*(synthesis\.json)$',
)


hyperspectral_parser_entry_point = HyperspectralParserEntryPoint(
    name='HyperspectralParser',
    description='Parser for hyperspectral ENVI datasets with .hdr/.bil cube files.',
    mainfile_name_re=r'.*(\.hdr)$',
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
    description='Parser for Mongo-shell experiment_plan.txt exports.',
    mainfile_name_re=r'(^|.*[/\\])experiment_plan\.txt$',
)


class SulfurizationParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.sulfurization_parser import (
            SulfurizationParser,
        )

        return SulfurizationParser(**self.dict())


sulfurization_parser_entry_point = SulfurizationParserEntryPoint(
    name='SulfurizationParser',
    description=(
        'Parser for PicoLog PLW sulfurization temperature measurements, '
        'holding-period detection and temperature stability analysis.'
    ),
    mainfile_name_re=r'(?i).*\.plw$',
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
