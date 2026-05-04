def test_parse_structured_valid_json():
    from services.rag import _parse_structured

    text = '{"reasoning": "test reasoning", "answer": "The total is $687.00", "citations": [1, 2]}'
    result = _parse_structured(text)
    assert result is not None
    assert result.reasoning == "test reasoning"
    assert result.answer == "The total is $687.00"
    assert result.citations == [1, 2]


def test_parse_structured_json_in_text():
    from services.rag import _parse_structured

    text = 'Here is my analysis:\n{"reasoning": "step by step", "answer": "Yes", "citations": [1]}\nDone.'
    result = _parse_structured(text)
    assert result is not None
    assert result.answer == "Yes"


def test_parse_structured_no_json():
    from services.rag import _parse_structured

    text = "This is just a plain text answer with no JSON at all."
    result = _parse_structured(text)
    assert result is None


def test_parse_structured_malformed_json():
    from services.rag import _parse_structured

    text = '{"reasoning": "incomplete...'
    result = _parse_structured(text)
    assert result is None


def test_generate_answer(mock_bedrock):
    from services.rag import generate_answer

    chunks = [
        {
            "patient_name": "WALKER, JAMES R",
            "section_name": "TOTALS",
            "text": "Total Billed: $687.00",
        }
    ]
    answer, tokens, structured, version = generate_answer("What is the total?", chunks)
    assert "687" in answer
    assert tokens > 0
    assert structured is not None
    assert version is not None
