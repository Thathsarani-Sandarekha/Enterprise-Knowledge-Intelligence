from openpyxl import Workbook
from app.services.extraction import extract_excel


def test_spreadsheet_provenance(tmp_path):
    path = tmp_path / 'materials.xlsx'
    workbook = Workbook()
    ws = workbook.active
    ws.title = 'Approved Materials'
    ws.append(['Item', 'Finish'])
    ws.append(['R-102', 'Porcelain tile'])
    workbook.save(path)
    chunks = extract_excel(path)
    assert len(chunks) == 1
    assert chunks[0].source_meta['cell_range'] == "'Approved Materials'!A1:B2"
    assert 'B2=Porcelain tile' in chunks[0].text
