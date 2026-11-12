"""Windows-safe NOMAD ELN matching parser used by this plugin."""

from pathlib import Path

from nomad.parsing.parser import ElnMatchingParser


class PortableElnMatchingParser(ElnMatchingParser):
    """ElnMatchingParser variant that handles Windows and POSIX raw paths."""

    @staticmethod
    def relative_path(mainfile, archive):
        """Return a source path relative to the upload's raw directory."""
        raw_root = Path(archive.m_context.raw_path()).resolve()
        source_path = Path(mainfile).resolve()
        try:
            return source_path.relative_to(raw_root).as_posix()
        except ValueError as exc:
            raise ValueError(
                f'Mainfile {mainfile!r} is outside the upload raw directory '
                f'{str(raw_root)!r}.'
            ) from exc

    def eln_name(self, mainfile, archive):
        relative_path = self.relative_path(mainfile, archive)
        return Path(relative_path).with_suffix('.archive.json').as_posix()

    def eln_section(self, mainfile, archive):
        return {
            'm_def': self.eln_m_def,
            'data_file': self.relative_path(mainfile, archive),
        }

    def parse(self, mainfile, archive, logger=None, child_archives=None):
        context = archive.m_context
        relative_path = self.relative_path(mainfile, archive)
        eln_name = self.eln_name(mainfile, archive)

        archive.m_update_from_dict(
            {
                'data': {
                    'm_def': self.raw_file_m_def,
                    'eln': f'{context.get_reference(eln_name)}#/data',
                    'data_type': self.data_type,
                    'file_ending': Path(mainfile).suffix,
                    'file_size': Path(mainfile).stat().st_size,
                }
            }
        )
        archive.metadata.entry_name = f'Data file {relative_path}'

        if not self.update and context.raw_path_exists(eln_name):
            return

        with context.update_entry(eln_name, write=True, process=True) as content:
            data = content.get('data', {})
            data.update(self.eln_section(mainfile, archive))
            content['data'] = data
