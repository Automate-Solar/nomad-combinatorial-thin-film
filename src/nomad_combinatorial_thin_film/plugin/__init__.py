from nomad.config.models.plugins import SchemaPackageEntryPoint


class ImageSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.image_plugin import m_package

        return m_package


class HyperspectralSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.hyperspectral_plugin import m_package

        return m_package


image_schema_package_entry_point = ImageSchemaPackageEntryPoint(
    name='ImagePlugin',
    description='Schema package for image analysis with metadata, ROI, and dimensions.',
)


hyperspectral_schema_package_entry_point = HyperspectralSchemaPackageEntryPoint(
    name='HyperspectralPlugin',
    description='Schema package for hyperspectral image datasets.',
)


schema_package_entry_point = image_schema_package_entry_point
