import pytest
from app.utils.json_parser import extract_json, JSONParsingError

def test_plain_valid_json():
    text = '{"key": "value"}'
    assert extract_json(text) == text

def test_markdown_wrapped_json():
    text = '```json\n{"key": "value"}\n```'
    assert extract_json(text) == '{"key": "value"}'

def test_json_with_explanatory_text():
    text = 'Here is the json you requested:\n{"key": "value"}\nHope this helps!'
    assert extract_json(text) == '{"key": "value"}'

def test_duplicated_model_output_fragments():
    text = '{"k\n{"key": "value"}'
    assert extract_json(text) == '{"key": "value"}'
    
    text = '{"claims": ["a"]} {"claims": ["a"]}'
    assert extract_json(text) == '{"claims": ["a"]}'

def test_truncated_incomplete_json():
    # With json_repair enabled for recovery, partial JSON is repaired
    assert extract_json('{"key": "val') == '{"key": "val"}'
    
    # Non-JSON text cannot be repaired into a valid dict/list
    text = 'just some text'
    with pytest.raises(JSONParsingError):
        extract_json(text)
