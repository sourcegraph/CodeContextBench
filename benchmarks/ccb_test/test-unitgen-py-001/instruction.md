# Task: Write Unit Tests for Django JSON Serializer

## Objective

Write comprehensive unit tests for Django's JSON serializer module located at `django/core/serializers/json.py`. The existing test file has been removed; you must write tests from scratch.

## Output

Write your test file to: `/workspace/test_json_serializer.py`

## What to Test

### Core Functionality
- **`Serializer.serialize()`**: Test serialization of Django model instances to JSON format. Verify correct JSON structure, field mapping, and output format options (indentation, ensuring ASCII, etc.).
- **`Deserializer()`**: Test deserialization of JSON strings back into Django model instances. Verify that deserialized objects have correct field values and model types.
- **`DjangoJSONEncoder`**: Test the custom JSON encoder's handling of Python types:
  - `datetime.date`, `datetime.time`, `datetime.datetime` (ISO format output)
  - `datetime.timedelta` (ISO 8601 duration format)
  - `decimal.Decimal` (string representation)
  - `uuid.UUID` (hyphenated string representation)
  - Lazy strings (`django.utils.functional.lazy`)

### Coverage Requirements
- **Round-trip serialization**: Serialize objects to JSON, then deserialize back, and verify the data matches the original.
- **Edge cases**:
  - Empty querysets / empty data lists
  - Null/None field values
  - Special characters and unicode strings
  - Error handling for invalid JSON input and malformed data
- **Both success and failure paths**: Include tests that verify correct behavior AND tests that verify appropriate exceptions are raised for invalid input.

## Constraints

- Use `django.test.TestCase` or Python's `unittest.TestCase` as the test base class.
- Use descriptive test method names that clearly indicate what is being tested (e.g., `test_serialize_datetime_field_outputs_iso_format`).
- All tests must pass `python3 -m py_compile` (valid Python syntax).
- Do NOT use pytest fixtures or third-party mocking libraries beyond `unittest.mock`.
- You may define simple model classes or use Django's built-in test infrastructure for model setup.

## Reference

Study the module under test at `django/core/serializers/json.py` to understand:
- The `Serializer` class and its `end_serialization()` method
- The `Deserializer` function and how it processes JSON streams
- The `DjangoJSONEncoder` class and its `default()` method for type handling
