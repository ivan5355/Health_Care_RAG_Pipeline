import re
import uuid

SECTION_HEADERS = [
    "PATIENT INFORMATION",
    "PROVIDER INFORMATION",
    "SERVICE LINES",
    "DIAGNOSIS CODES",
    "TOTALS",
    "REMARKS",
]

DEFAULT_MAX_CHUNK_SIZE = 500
DEFAULT_OVERLAP_SIZE = 50


def extract_patient_name(raw_text: str) -> str:
    match = re.search(r"Name:\s*(.+?)(?:\s{2,}|$)", raw_text)
    if match:
        return match.group(1).strip()
    return "Unknown"


def _split_section_with_overlap(
    text: str,
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    overlap_size: int = DEFAULT_OVERLAP_SIZE,
) -> list[str]:
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chunk_size
        if end < len(text):
            newline_pos = text.rfind("\n", start, end)
            if newline_pos > start:
                end = newline_pos + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap_size
    return chunks


def chunk_eob_by_section(
    document_id: str,
    raw_text: str,
    max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE,
    overlap_size: int = DEFAULT_OVERLAP_SIZE,
) -> list[dict]:
    lines = raw_text.strip().split("\n")

    header_positions = []
    for i, line in enumerate(lines):
        stripped = line.strip().rstrip(":")
        if stripped in SECTION_HEADERS:
            header_positions.append((i, stripped))

    chunks: list[dict] = []

    if header_positions and header_positions[0][0] > 0:
        header_text = "\n".join(lines[: header_positions[0][0]]).strip()
        if header_text:
            for sub in _split_section_with_overlap(header_text, max_chunk_size, overlap_size):
                chunks.append(
                    {
                        "id": f"{document_id}_chunk_{uuid.uuid4().hex[:8]}",
                        "document_id": document_id,
                        "section_name": "Header",
                        "text": sub,
                        "chunk_index": len(chunks),
                    }
                )

    for idx, (line_num, section_name) in enumerate(header_positions):
        end_line = header_positions[idx + 1][0] if idx + 1 < len(header_positions) else len(lines)

        section_text = "\n".join(lines[line_num:end_line]).strip()

        footer_markers = ["THIS IS NOT A BILL", "Processed by"]
        cleaned_lines = []
        for sl in section_text.split("\n"):
            if any(marker in sl for marker in footer_markers):
                break
            cleaned_lines.append(sl)
        section_text = "\n".join(cleaned_lines).strip()

        if section_text:
            for sub in _split_section_with_overlap(section_text, max_chunk_size, overlap_size):
                chunks.append(
                    {
                        "id": f"{document_id}_chunk_{uuid.uuid4().hex[:8]}",
                        "document_id": document_id,
                        "section_name": section_name,
                        "text": sub,
                        "chunk_index": len(chunks),
                    }
                )

    return chunks
