# Property-Based Tests for Database Schema

## Overview

This directory contains property-based tests for the database schema, specifically testing round-trip consistency for meeting configuration stored in JSONB columns.

**Validates: Requirements 25.4**

## Test File

- `test_property_roundtrip.py` - Property tests for meeting configuration serialization/deserialization

## What These Tests Validate

The property tests ensure that meeting configuration objects can be:
1. Serialized to JSON
2. Stored in PostgreSQL as JSONB
3. Retrieved from the database
4. Deserialized back to Python objects
5. **Without any data loss or corruption**

## Test Coverage

The property tests cover:

### 1. **Comprehensive Meeting Configuration Round-Trip** (100 examples)
- Tests arbitrary meeting configurations with various field combinations
- Validates video quality settings, feature flags, numeric settings, string settings
- Tests nested objects (audio_settings, video_settings)
- Tests arrays (allowed_domains)
- Tests edge cases: empty strings, special characters, unicode, null values

### 2. **Empty Configuration Round-Trip** (50 examples)
- Ensures empty configurations `{}` are handled correctly

### 3. **Primitive Types Round-Trip** (50 examples)
- Tests all JSON primitive types: string, number, boolean, null
- Validates each type is preserved exactly

### 4. **Nested Objects Round-Trip** (20 examples)
- Tests deeply nested configuration objects (1-5 levels deep)
- Ensures nested structure is preserved

### 5. **Array Round-Trip** (50 examples)
- Tests arrays with mixed element types
- Validates array length and element values

### 6. **Unicode and Special Characters**
- Tests unicode characters (你好世界)
- Tests emojis (👋🌍🎉)
- Tests special characters (newlines, tabs, quotes, backslashes)
- Tests mixed special symbols (™ © ® € £ ¥)

## Prerequisites

### 1. PostgreSQL Database

You need a running PostgreSQL database. You can start it using Docker:

```bash
# Start PostgreSQL using docker-compose
docker compose up -d postgres

# Wait for database to be ready
docker compose ps postgres
```

Or install PostgreSQL locally and ensure it's running on `localhost:5432`.

### 2. Database Schema

Initialize the database schema:

```bash
# From the project root
python backend/database/init_db.py init
```

### 3. Python Dependencies

Install required packages:

```bash
pip install -r backend/requirements.txt
```

Key dependencies:
- `pytest>=7.4.0` - Testing framework
- `hypothesis>=6.92.0` - Property-based testing library
- `psycopg2-binary>=2.9.9` - PostgreSQL adapter

### 4. Environment Variables

Ensure your `.env` file has the correct database URL:

```env
DATABASE_URL=postgresql://meeting_user:meeting_pass@localhost:5432/meeting_db
```

## Running the Tests

### Run All Property Tests

```bash
# From the project root
python -m pytest backend/database/test_property_roundtrip.py -v
```

### Run Specific Test

```bash
# Run only the main round-trip test
python -m pytest backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_meeting_config_roundtrip -v

# Run only the unicode test
python -m pytest backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_unicode_and_special_characters -v
```

### Run with More Examples

Hypothesis generates random test cases. You can increase the number of examples:

```bash
# Run with 500 examples instead of default 100
python -m pytest backend/database/test_property_roundtrip.py -v --hypothesis-seed=random --hypothesis-show-statistics
```

### Run with Specific Seed (for reproducibility)

If a test fails, Hypothesis will print a seed. You can reproduce the failure:

```bash
python -m pytest backend/database/test_property_roundtrip.py -v --hypothesis-seed=12345
```

## Expected Output

When all tests pass, you should see:

```
backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_meeting_config_roundtrip PASSED
backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_empty_config_roundtrip PASSED
backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_primitive_types_roundtrip PASSED
backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_nested_objects_roundtrip PASSED
backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_array_roundtrip PASSED
backend/database/test_property_roundtrip.py::TestMeetingConfigRoundTrip::test_unicode_and_special_characters PASSED

============================== 6 passed in X.XXs ==============================
```

## Understanding Property-Based Testing

Unlike traditional unit tests that test specific examples, property-based tests:

1. **Generate random test cases** - Hypothesis automatically generates diverse test inputs
2. **Test universal properties** - Verify properties that should hold for ALL inputs
3. **Find edge cases** - Automatically discover edge cases you might not think of
4. **Shrink failures** - When a test fails, Hypothesis simplifies the input to the minimal failing case

### Example Property

**Property**: For any valid meeting configuration, serializing then deserializing produces an equivalent object.

**Traditional Test** (specific example):
```python
def test_specific_config():
    config = {"video_quality": "720p", "enable_chat": True}
    # ... test this one case
```

**Property Test** (universal property):
```python
@given(config=meeting_config_strategy())
def test_any_config(config):
    # Tests 100 different random configurations automatically
    # ... test the property holds for ALL of them
```

## Troubleshooting

### Database Connection Error

```
Error: connection to server at "localhost", port 5432 failed
```

**Solution**: Start PostgreSQL:
```bash
docker compose up -d postgres
```

### Module Not Found Error

```
ModuleNotFoundError: No module named 'hypothesis'
```

**Solution**: Install dependencies:
```bash
pip install hypothesis>=6.92.0
```

### Test Failures

If a property test fails, Hypothesis will show you:
1. The failing input that caused the failure
2. A simplified (shrunk) version of the input
3. The seed to reproduce the failure

Example:
```
Falsifying example: test_meeting_config_roundtrip(
    config={'video_quality': '720p', 'enable_chat': True}
)
You can reproduce this example by temporarily adding @reproduce_failure('6.151.9', b'...')
```

## Integration with CI/CD

These tests should be run in your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run property tests
  run: |
    docker compose up -d postgres
    python backend/database/init_db.py init
    python -m pytest backend/database/test_property_roundtrip.py -v
```

## Further Reading

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://hypothesis.works/articles/what-is-property-based-testing/)
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
