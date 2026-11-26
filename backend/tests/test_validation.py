from io import BytesIO
from zipfile import ZipFile
import pytest
from fastapi import HTTPException
from app.services.validation import inspect_upload


def test_pdf_header_and_unsafe_suffix():
    assert inspect_upload('sample.pdf', b'%PDF-1.7\nhello')[0] == 'sample.pdf'
    with pytest.raises(HTTPException) as exc:
        inspect_upload('malicious.exe', b'MZ')
    assert exc.value.status_code == 415
    with pytest.raises(HTTPException):
        inspect_upload('fake.pdf', b'not a pdf')


def test_valid_office_package():
    bio = BytesIO()
    with ZipFile(bio, 'w') as archive:
        archive.writestr('[Content_Types].xml', '<Types/>')
        archive.writestr('xl/workbook.xml', '<workbook/>')
    assert inspect_upload('demo.xlsx', bio.getvalue())[0] == 'demo.xlsx'
