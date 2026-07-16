from nomad.config.models.plugins import ParserEntryPoint


class ImageParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.image_parser import DataRootParser

        return DataRootParser(**self.dict())


class HyperspectralParserEntryPoint(ParserEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.parser.hyperspectral_parser import HyperspectralRootParser

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
