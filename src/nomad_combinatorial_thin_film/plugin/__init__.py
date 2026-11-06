from nomad.config.models.plugins import SchemaPackageEntryPoint


class ImageSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.image_plugin import m_package

        return m_package


class HyperspectralSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.hyperspectral_plugin import m_package

        return m_package


class SputteringSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.sputter import m_package

        return m_package


class XrdSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.xrd_plugin import m_package

        return m_package


image_schema_package_entry_point = ImageSchemaPackageEntryPoint(
    name='ImagePlugin',
    description='Schema package for image analysis with metadata, ROI, and dimensions.',
)


hyperspectral_schema_package_entry_point = HyperspectralSchemaPackageEntryPoint(
    name='HyperspectralPlugin',
    description='Schema package for hyperspectral image datasets.',
)


sputtering_schema_package_entry_point = SputteringSchemaPackageEntryPoint(
    name='UppsalaSputteringPlugin',
    description='Schema package for Uppsala sputtering data.',
)

xrd_schema_package_entry_point = XrdSchemaPackageEntryPoint(
    name='DTUXRDMeasurement',
    description='Schema package for DTU X-ray diffraction measurements.',
)


schema_package_entry_point = image_schema_package_entry_point


class ExperimentPlanSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.experiment_plan import m_package

        return m_package


experiment_plan_schema_package_entry_point = ExperimentPlanSchemaPackageEntryPoint(
    name='UppsalaSputteringExperimentPlan',
    description='Schema package for sputtering experiment plans and predicted profiles.',
)


class SulfurizationSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.sulfurization import (
            m_package,
        )

        return m_package


sulfurization_schema_package_entry_point = SulfurizationSchemaPackageEntryPoint(
    name='SulfurizationSchema',
    description=(
        'Schema for PicoLog sulfurization measurements '
        'and temperature stability analysis.'
    ),
)


class XRDSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_combinatorial_thin_film.plugin.xrd import m_package

        return m_package


xrd_schema_package_entry_point = XRDSchemaPackageEntryPoint(
    name='XRDSchema',
    description=(
        'Schema for spatially resolved XRD measurements '
        'and experimental peak detection.'
    ),
)
