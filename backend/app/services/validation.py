"""File extension, signature, and OOXML archive checks.

These checks reduce accidental and common malicious uploads, but are not a
replacement for OS-level sandboxing and resource-limited document parsing.
"""
from io import BytesIO
from pathlib import Path, PureWindowsPath
from zipfile import BadZipFile, ZipFile
from fastapi import HTTPException
from app.config import MAX_UPLOAD_BYTES

MEDIA_TYPES = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}


def inspect_upload(filename: str | None, data: bytes) -> tuple[str, str]:
    if not filename:
        raise HTTPException(400, 'Filename is required')
    # Upload browsers may send either Windows or POSIX path separators.
    clean = PureWindowsPath(filename.replace('/', '\\')).name.strip()
    if not clean or len(clean) > 255 or any(ord(c) < 32 for c in clean):
        raise HTTPException(400, 'Invalid filename')
    extension = Path(clean).suffix.lower()
    if extension not in MEDIA_TYPES:
        raise HTTPException(415, 'Only PDF, DOCX and XLSX files are supported')
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, 'File is empty or exceeds the 15 MiB limit')
    if extension == '.pdf':
        if not data.startswith(b'%PDF-'):
            raise HTTPException(415, 'Invalid PDF signature')
    else:
        if not data.startswith(b'PK'):
            raise HTTPException(415, 'Invalid Office file signature')
        try:
            with ZipFile(BytesIO(data)) as archive:
                members = archive.infolist()
                names = set(archive.namelist())
                expected = 'word/document.xml' if extension == '.docx' else 'xl/workbook.xml'
                if '[Content_Types].xml' not in names or expected not in names:
                    raise HTTPException(415, 'Invalid Office package')
                if len(members) > 3000 or sum(info.file_size for info in members) > 100 * 1024 * 1024:
                    raise HTTPException(413, 'Office package exceeds unpacked size limits')
                if any(info.flag_bits & 1 for info in members):
                    raise HTTPException(415, 'Encrypted Office archives are unsupported')
        except BadZipFile as exc:
            raise HTTPException(415, 'Invalid Office ZIP container') from exc
    return clean, MEDIA_TYPES[extension]
