from services.chunker import _split_section_with_overlap, chunk_eob_by_section, extract_patient_name

SAMPLE_EOB = """PATIENT INFORMATION
Name: WALKER, JAMES R   DOB: 08/14/1952
Member ID: XYZ123456

SERVICE LINES
Date       Code    Description         Billed    Allowed   Copay
01/15/24   99213   Office Visit        $250.00   $180.00   $30.00
01/15/24   85025   CBC Blood Test      $87.00    $65.00    $0.00

DIAGNOSIS CODES
E11.9  Type 2 diabetes mellitus without complications
I10    Essential hypertension

TOTALS
Total Billed: $687.00
Total Allowed: $485.00
Patient Responsibility: $30.00

REMARKS
THIS IS NOT A BILL
Processed by Aetna Claims Department
"""


def test_extract_patient_name_standard():
    text = "Name: WALKER, JAMES R   DOB: 08/14/1952"
    assert extract_patient_name(text) == "WALKER, JAMES R"


def test_extract_patient_name_missing():
    text = "No name field here"
    assert extract_patient_name(text) == "Unknown"


def test_split_section_short_text():
    text = "Short text that fits in one chunk"
    result = _split_section_with_overlap(text, max_chunk_size=500)
    assert len(result) == 1
    assert result[0] == text


def test_split_section_long_text():
    text = "A" * 1200
    result = _split_section_with_overlap(text, max_chunk_size=500, overlap_size=50)
    assert len(result) > 1
    assert all(len(chunk) <= 500 for chunk in result)


def test_chunk_eob_by_section_produces_sections():
    chunks = chunk_eob_by_section("doc_1", SAMPLE_EOB)
    section_names = [c["section_name"] for c in chunks]
    assert "PATIENT INFORMATION" in section_names
    assert "SERVICE LINES" in section_names
    assert "TOTALS" in section_names
    assert "DIAGNOSIS CODES" in section_names


def test_chunk_eob_by_section_structure():
    chunks = chunk_eob_by_section("doc_1", SAMPLE_EOB)
    for chunk in chunks:
        assert "id" in chunk
        assert "document_id" in chunk
        assert "section_name" in chunk
        assert "text" in chunk
        assert "chunk_index" in chunk
        assert chunk["document_id"] == "doc_1"


def test_chunk_eob_by_section_removes_footer():
    chunks = chunk_eob_by_section("doc_1", SAMPLE_EOB)
    all_text = " ".join(c["text"] for c in chunks)
    assert "THIS IS NOT A BILL" not in all_text
    assert "Processed by" not in all_text


def test_chunk_eob_by_section_empty_input():
    chunks = chunk_eob_by_section("doc_1", "")
    assert chunks == []


def test_chunk_eob_by_section_no_headers():
    text = "Just some plain text with no section headers"
    chunks = chunk_eob_by_section("doc_1", text)
    assert chunks == []
