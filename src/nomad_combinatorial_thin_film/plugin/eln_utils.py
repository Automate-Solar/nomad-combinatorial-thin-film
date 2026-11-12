"""Utilities shared by the editable parser-generated ELN schemas."""

from pathlib import Path


def get_source_path(archive, data_file):
    """Resolve an ELN data_file path to its local upload path."""
    return Path(archive.m_context.raw_path()) / data_file


def register_derived_upload_file(archive, relative_path):
    """Register a generated file so NOMAD can serve it from the upload."""
    if not relative_path:
        return

    raw_path = Path(archive.m_context.raw_path()) / relative_path
    if raw_path.is_file():
        try:
            archive.m_context.process_updated_raw_file(
                relative_path,
                allow_modify=True,
            )
        except NotImplementedError:
            # Client-side contexts do not register changes in upload storage.
            return


def replace_section_data(target, source, preserved_names):
    """Replace source-derived values while leaving ELN-only fields intact."""
    preserved_names = set(preserved_names)

    for name, quantity in target.m_def.all_quantities.items():
        if name in preserved_names:
            continue
        target.m_set(quantity, source.m_get(quantity))

    for name, sub_section in target.m_def.all_sub_sections.items():
        if name in preserved_names:
            continue

        if sub_section.repeats:
            values = source.m_get_sub_sections(sub_section)
            setattr(
                target,
                name,
                [value.m_copy(deep=True) for value in values],
            )
            continue

        value = source.m_get_sub_section(sub_section, 0)
        setattr(target, name, value.m_copy(deep=True) if value is not None else None)
