"""
Property-based tests for database schema round-trip consistency.

**Validates: Requirements 25.4**

This module tests that meeting configuration objects can be serialized to JSONB,
stored in the database, retrieved, and deserialized back to equivalent objects
without data loss.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import psycopg2
import pytest
from hypothesis import given, settings, strategies as st

# Import database utilities
sys.path.insert(0, str(Path(__file__).parent))
from init_db import get_database_url, parse_database_url


# Strategy for generating valid meeting configuration objects
@st.composite
def meeting_config_strategy(draw):
    """
    Generate arbitrary meeting configuration objects for property testing.
    
    This strategy creates diverse meeting configurations with various field
    combinations to test round-trip serialization comprehensively.
    """
    config = {}
    
    # Video quality settings
    if draw(st.booleans()):
        config['video_quality'] = draw(st.sampled_from(['360p', '480p', '720p', '1080p', '4k']))
    
    # Boolean feature flags
    if draw(st.booleans()):
        config['enable_chat'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_screen_sharing'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_captions'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_sign_language'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_recording'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_whiteboard'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_breakout_rooms'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_waiting_room'] = draw(st.booleans())
    if draw(st.booleans()):
        config['enable_polls'] = draw(st.booleans())
    
    # Numeric settings
    if draw(st.booleans()):
        config['max_participants'] = draw(st.integers(min_value=2, max_value=1000))
    if draw(st.booleans()):
        config['recording_quality'] = draw(st.integers(min_value=1, max_value=10))
    if draw(st.booleans()):
        config['audio_bitrate'] = draw(st.integers(min_value=64, max_value=320))
    if draw(st.booleans()):
        config['video_bitrate'] = draw(st.integers(min_value=500, max_value=8000))
    
    # String settings with special characters and unicode
    if draw(st.booleans()):
        config['sign_language'] = draw(st.sampled_from(['ASL', 'BSL', 'ISL', 'JSL', 'CSL']))
    if draw(st.booleans()):
        config['language'] = draw(st.sampled_from(['en', 'es', 'fr', 'de', 'zh', 'ja', 'ar']))
    if draw(st.booleans()):
        config['timezone'] = draw(st.sampled_from([
            'UTC', 'America/New_York', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney'
        ]))
    
    # Nested objects
    if draw(st.booleans()):
        config['audio_settings'] = {
            'noise_cancellation': draw(st.booleans()),
            'echo_cancellation': draw(st.booleans()),
            'auto_gain_control': draw(st.booleans()),
        }
    
    if draw(st.booleans()):
        config['video_settings'] = {
            'background_blur': draw(st.booleans()),
            'virtual_background': draw(st.booleans()),
            'mirror_video': draw(st.booleans()),
        }
    
    # Arrays
    if draw(st.booleans()):
        config['allowed_domains'] = draw(st.lists(
            st.text(alphabet=st.characters(whitelist_categories=('L', 'N')), min_size=3, max_size=20),
            min_size=0,
            max_size=10
        ))
    
    # Edge cases: empty strings, special characters, unicode
    if draw(st.booleans()):
        config['custom_branding'] = draw(st.text(max_size=100))
    
    # Floating point numbers
    if draw(st.booleans()):
        config['confidence_threshold'] = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False))
    
    # Null values
    if draw(st.booleans()):
        config['custom_field'] = None
    
    return config


class TestMeetingConfigRoundTrip:
    """
    Property-based tests for meeting configuration round-trip consistency.
    
    **Validates: Requirements 25.4**
    """
    
    @pytest.fixture(scope="class")
    def db_connection(self):
        """Create a database connection for testing."""
        db_url = get_database_url()
        conn_params = parse_database_url(db_url)
        conn = psycopg2.connect(**conn_params)
        yield conn
        conn.close()
    
    @pytest.fixture(autouse=True)
    def setup_test_meeting(self, db_connection):
        """Create a test meeting for each test."""
        cursor = db_connection.cursor()
        
        # Create a test user
        cursor.execute("""
            INSERT INTO users (id, email, name)
            VALUES ('00000000-0000-0000-0000-000000000001', 'test@example.com', 'Test User')
            ON CONFLICT (id) DO NOTHING;
        """)
        
        # Create a test meeting
        cursor.execute("""
            INSERT INTO meetings (id, title, host_id, settings)
            VALUES ('00000000-0000-0000-0000-000000000002', 'Test Meeting', 
                    '00000000-0000-0000-0000-000000000001', '{}'::jsonb)
            ON CONFLICT (id) DO UPDATE SET settings = '{}'::jsonb;
        """)
        
        db_connection.commit()
        cursor.close()
        
        yield
        
        # Cleanup is handled by the class-level fixture
    
    @given(config=meeting_config_strategy())
    @settings(max_examples=100, deadline=None)
    def test_meeting_config_roundtrip(self, db_connection, config: Dict[str, Any]):
        """
        Property Test: Round-trip consistency for meeting configuration.
        
        **Validates: Requirements 25.4**
        
        For any valid meeting configuration object:
        1. Serialize to JSON
        2. Store in database as JSONB
        3. Retrieve from database
        4. Deserialize from JSON
        5. Verify the result equals the original
        
        This ensures no data loss during serialization/deserialization cycles.
        """
        cursor = db_connection.cursor()
        
        try:
            # Step 1: Serialize configuration to JSON
            serialized = json.dumps(config, sort_keys=True)
            
            # Step 2: Store in database as JSONB
            cursor.execute("""
                UPDATE meetings
                SET settings = %s::jsonb
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """, (serialized,))
            db_connection.commit()
            
            # Step 3: Retrieve from database
            cursor.execute("""
                SELECT settings
                FROM meetings
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """)
            result = cursor.fetchone()
            assert result is not None, "Meeting not found in database"
            
            retrieved_jsonb = result[0]
            
            # Step 4: Deserialize from JSON
            deserialized = json.loads(json.dumps(retrieved_jsonb))
            
            # Step 5: Verify equivalence
            # Sort keys for consistent comparison
            original_sorted = json.dumps(config, sort_keys=True)
            deserialized_sorted = json.dumps(deserialized, sort_keys=True)
            
            assert original_sorted == deserialized_sorted, (
                f"Round-trip failed!\n"
                f"Original:     {original_sorted}\n"
                f"Deserialized: {deserialized_sorted}"
            )
            
        finally:
            cursor.close()
    
    @given(config=meeting_config_strategy())
    @settings(max_examples=50, deadline=None)
    def test_empty_config_roundtrip(self, db_connection, config: Dict[str, Any]):
        """
        Property Test: Empty configuration round-trip.
        
        **Validates: Requirements 25.4**
        
        Test that empty configurations are handled correctly.
        """
        cursor = db_connection.cursor()
        
        try:
            empty_config = {}
            serialized = json.dumps(empty_config)
            
            cursor.execute("""
                UPDATE meetings
                SET settings = %s::jsonb
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """, (serialized,))
            db_connection.commit()
            
            cursor.execute("""
                SELECT settings
                FROM meetings
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """)
            result = cursor.fetchone()
            retrieved = result[0]
            
            assert retrieved == {}, f"Empty config not preserved: {retrieved}"
            
        finally:
            cursor.close()
    
    @given(
        text=st.text(min_size=0, max_size=1000),
        number=st.floats(allow_nan=False, allow_infinity=False),
        boolean=st.booleans()
    )
    @settings(max_examples=50, deadline=None)
    def test_primitive_types_roundtrip(self, db_connection, text: str, number: float, boolean: bool):
        """
        Property Test: Primitive data types round-trip.
        
        **Validates: Requirements 25.4**
        
        Test that all JSON primitive types (string, number, boolean, null) 
        are preserved through round-trip serialization.
        """
        cursor = db_connection.cursor()
        
        try:
            config = {
                'text_field': text,
                'number_field': number,
                'boolean_field': boolean,
                'null_field': None
            }
            
            serialized = json.dumps(config, sort_keys=True)
            
            cursor.execute("""
                UPDATE meetings
                SET settings = %s::jsonb
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """, (serialized,))
            db_connection.commit()
            
            cursor.execute("""
                SELECT settings
                FROM meetings
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """)
            result = cursor.fetchone()
            retrieved = result[0]
            
            # Verify each field
            assert retrieved['text_field'] == text
            assert retrieved['number_field'] == number or (
                # Handle NaN case
                retrieved['number_field'] != retrieved['number_field'] and 
                number != number
            )
            assert retrieved['boolean_field'] == boolean
            assert retrieved['null_field'] is None
            
        finally:
            cursor.close()
    
    @given(depth=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20, deadline=None)
    def test_nested_objects_roundtrip(self, db_connection, depth: int):
        """
        Property Test: Nested objects round-trip.
        
        **Validates: Requirements 25.4**
        
        Test that deeply nested configuration objects are preserved.
        """
        cursor = db_connection.cursor()
        
        try:
            # Create nested structure
            config = {'value': 'root'}
            current = config
            for i in range(depth):
                current['nested'] = {'value': f'level_{i}'}
                current = current['nested']
            
            serialized = json.dumps(config, sort_keys=True)
            
            cursor.execute("""
                UPDATE meetings
                SET settings = %s::jsonb
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """, (serialized,))
            db_connection.commit()
            
            cursor.execute("""
                SELECT settings
                FROM meetings
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """)
            result = cursor.fetchone()
            retrieved = result[0]
            
            # Verify nested structure
            original_sorted = json.dumps(config, sort_keys=True)
            retrieved_sorted = json.dumps(retrieved, sort_keys=True)
            assert original_sorted == retrieved_sorted
            
        finally:
            cursor.close()
    
    @given(
        items=st.lists(
            st.one_of(
                st.text(max_size=50),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.none()
            ),
            min_size=0,
            max_size=20
        )
    )
    @settings(max_examples=50, deadline=None)
    def test_array_roundtrip(self, db_connection, items: list):
        """
        Property Test: Array round-trip.
        
        **Validates: Requirements 25.4**
        
        Test that arrays with various element types are preserved.
        """
        cursor = db_connection.cursor()
        
        try:
            config = {'items': items}
            serialized = json.dumps(config, sort_keys=True)
            
            cursor.execute("""
                UPDATE meetings
                SET settings = %s::jsonb
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """, (serialized,))
            db_connection.commit()
            
            cursor.execute("""
                SELECT settings
                FROM meetings
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """)
            result = cursor.fetchone()
            retrieved = result[0]
            
            assert len(retrieved['items']) == len(items)
            for original, retrieved_item in zip(items, retrieved['items']):
                if isinstance(original, float) and original != original:  # NaN check
                    assert retrieved_item != retrieved_item
                else:
                    assert retrieved_item == original
            
        finally:
            cursor.close()
    
    def test_unicode_and_special_characters(self, db_connection):
        """
        Property Test: Unicode and special characters round-trip.
        
        **Validates: Requirements 25.4**
        
        Test that unicode characters, emojis, and special characters are preserved.
        """
        cursor = db_connection.cursor()
        
        try:
            config = {
                'unicode': '你好世界',
                'emoji': '👋🌍🎉',
                'special': 'Line1\nLine2\tTabbed',
                'quotes': 'He said "Hello"',
                'backslash': 'C:\\Users\\Test',
                'mixed': 'Test™ © ® € £ ¥'
            }
            
            serialized = json.dumps(config, sort_keys=True, ensure_ascii=False)
            
            cursor.execute("""
                UPDATE meetings
                SET settings = %s::jsonb
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """, (serialized,))
            db_connection.commit()
            
            cursor.execute("""
                SELECT settings
                FROM meetings
                WHERE id = '00000000-0000-0000-0000-000000000002';
            """)
            result = cursor.fetchone()
            retrieved = result[0]
            
            for key, value in config.items():
                assert retrieved[key] == value, f"Mismatch for {key}: {retrieved[key]} != {value}"
            
        finally:
            cursor.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
