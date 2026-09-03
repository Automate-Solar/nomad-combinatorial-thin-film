from nomad.metainfo.metainfo import Package

from nomad_combinatorial_thin_film.plugin import schema_package_entry_point


def test_schema_package_entry_point_loads():
    package = schema_package_entry_point.load()
    assert isinstance(package, Package)
    assert 'Image Analysis' in package.name
