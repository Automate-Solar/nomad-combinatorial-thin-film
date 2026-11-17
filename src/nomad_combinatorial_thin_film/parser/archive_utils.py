"""ZIP archive matching and extraction helpers shared by parser plugins."""

import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

from nomad.parsing.parser import MatchingParser


def _zip_members(filename):
    try:
        with zipfile.ZipFile(filename) as archive:
            return [name.replace('\\', '/').lower() for name in archive.namelist()]
    except (OSError, zipfile.BadZipFile):
        return []


def archive_has_members(filename, kind):
    """Check the archive contents to avoid matching unrelated generic ZIPs."""
    members = _zip_members(filename)
    matchers = {
        'image': lambda: any(Path(name).name == 'synthesis.json' for name in members),
        'hyperspectral': lambda: (
            any(name.endswith('.hdr') for name in members)
            and any(name.endswith('.bil') for name in members)
        ),
        'sulfurization': lambda: any(name.endswith('.plw') for name in members),
        'experiment_plan': lambda: any(
            Path(name).name == 'experiment_plan.txt' for name in members
        ),
        'xrd': lambda: any(name.endswith(('.asc', '.xrdml')) for name in members),
        'rtp': lambda: _archive_contains_rtp_json(filename),
    }
    matcher = matchers.get(kind)
    return bool(matcher and matcher())


def _archive_contains_rtp_json(filename):
    try:
        with zipfile.ZipFile(filename) as archive:
            for name in archive.namelist():
                if not name.lower().endswith('.json'):
                    continue
                with archive.open(name) as member:
                    if b'"run_id"' in member.read(16384):
                        return True
            return False
    except (OSError, zipfile.BadZipFile, KeyError, RuntimeError):
        return False


def read_zip_member(filename, suffix, contains: bytes | None = None):
    """Read the first regular ZIP member matching a filename suffix."""
    with zipfile.ZipFile(filename) as archive:
        matches = []
        for name in archive.namelist():
            if not name.lower().endswith(suffix.lower()) or name.endswith('/'):
                continue
            if contains is None:
                matches.append(name)
            else:
                with archive.open(name) as member:
                    if contains in member.read(16384):
                        matches.append(name)
        if not matches:
            raise FileNotFoundError(f'No {suffix} file was found in {filename!r}.')
        return archive.read(matches[0])


class ZipAwareMatchingParser(MatchingParser):
    """Match modality-specific ZIP archives without claiming unrelated ZIPs."""

    archive_kind = ''
    archive_extensions = ('.zip',)

    def is_mainfile(
        self,
        filename,
        mime,
        buffer,
        decoded_buffer,
        compression=None,
    ):
        normalized = str(filename).replace('\\', '/').lower()
        if '/__nomad_extracted__/' in normalized:
            return False
        if normalized.endswith(self.archive_extensions):
            return bool(
                self._mainfile_name_re.fullmatch(filename)
                and archive_has_members(filename, self.archive_kind)
            )
        return super().is_mainfile(
            filename,
            mime,
            buffer,
            decoded_buffer,
            compression,
        )


def normalize_raw_path(path):
    """Return a slash-normalized path relative to an upload's raw directory."""
    normalized = str(path).replace('\\', '/')
    if '/raw/' in normalized:
        return normalized.split('/raw/', 1)[1]
    if normalized.startswith('raw/'):
        return normalized[4:]
    return normalized.lstrip('/')


def extract_zip_to_upload(context, archive_path):
    """Extract a ZIP beneath the upload raw directory and return member paths.

    The private extraction directory is excluded from parser matching. Keeping
    extracted source files in raw storage lets existing path-based parsers and
    ELN file references work without changing their data model.
    """
    relative_archive = normalize_raw_path(archive_path)
    archive_relative = PurePosixPath(relative_archive)
    extracted_root = (
        PurePosixPath('__nomad_extracted__')
        / archive_relative.parent
        / archive_relative.stem
    )
    raw_root = Path(context.raw_path())
    output_root = raw_root.joinpath(*extracted_root.parts)
    output_root.mkdir(parents=True, exist_ok=True)

    extracted = []
    with context.raw_file(relative_archive, 'rb') as source:
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                member = PurePosixPath(info.filename.replace('\\', '/'))
                mode = info.external_attr >> 16
                if (
                    info.is_dir()
                    or stat.S_ISLNK(mode)
                    or member.is_absolute()
                    or '..' in member.parts
                ):
                    continue
                destination = extracted_root / member
                destination_path = raw_root.joinpath(*destination.parts)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                relative_destination = destination.as_posix()
                with archive.open(info) as member_file:
                    with context.raw_file(relative_destination, 'wb') as output:
                        shutil.copyfileobj(member_file, output, length=1024 * 1024)
                try:
                    context.process_updated_raw_file(
                        relative_destination,
                        allow_modify=True,
                    )
                except NotImplementedError:
                    pass
                extracted.append(destination_path)
    return extracted
