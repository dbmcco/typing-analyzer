# ABOUTME: Unit tests for utility functions and data structures
import pytest
import tempfile
import json
from datetime import datetime
from pathlib import Path

from src.utils import (
    KeystrokeEvent, ConfigManager, DataManager,
    get_finger_for_key, calculate_wpm, detect_typing_burst
)

class TestKeystrokeEvent:
    """Test KeystrokeEvent data structure."""
    
    def test_keystroke_event_creation(self):
        """Test creating a keystroke event."""
        event = KeystrokeEvent(
            timestamp=1234567890.123,
            key_code=65,
            key_char='a',
            key_name='a',
            dwell_time=0.1,
            time_since_last=0.2,
            app_name='TextEdit',
            window_title='Document.txt',
            session_id='test-session',
            is_correction=False,
            pause_before=0.05,
            typing_burst=True
        )
        
        assert event.timestamp == 1234567890.123
        assert event.key_char == 'a'
        assert event.app_name == 'TextEdit'
        assert event.typing_burst is True
    
    def test_keystroke_event_serialization(self):
        """Test event serialization to/from dict."""
        original = KeystrokeEvent(
            timestamp=1234567890.123,
            key_code=65,
            key_char='a',
            key_name='a',
            dwell_time=0.1,
            time_since_last=0.2,
            app_name='TextEdit',
            window_title='Document.txt',
            session_id='test-session',
            is_correction=False,
            pause_before=0.05,
            typing_burst=True,
            finger_assignment='left_pinky'
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = KeystrokeEvent.from_dict(data)
        
        assert restored.timestamp == original.timestamp
        assert restored.key_char == original.key_char
        assert restored.finger_assignment == original.finger_assignment

class TestConfigManager:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test loading default configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
collection:
  sample_rate_hz: 500
  buffer_size: 5000
analysis:
  hesitation_threshold: 1.0
            """)
            config_path = f.name
        
        try:
            config = ConfigManager(config_path)
            assert config.get('collection.sample_rate_hz') == 500
            assert config.get('analysis.hesitation_threshold') == 1.0
            assert config.get('nonexistent.key', 'default') == 'default'
        finally:
            Path(config_path).unlink()
    
    def test_missing_config_file(self):
        """Test behavior with missing config file."""
        config = ConfigManager('nonexistent.yaml')
        # Should use defaults
        assert config.get('collection.sample_rate_hz') == 1000
        assert config.get('analysis.hesitation_threshold') == 0.8

class TestDataManager:
    """Test data storage and retrieval."""
    
    def test_data_storage_and_loading(self):
        """Test storing and loading keystroke data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_manager = DataManager(temp_dir)
            
            # Create test events
            events = [
                KeystrokeEvent(
                    timestamp=1234567890.0 + i,
                    key_code=65 + i,
                    key_char=chr(65 + i),
                    key_name=chr(65 + i),
                    dwell_time=0.1,
                    time_since_last=0.2,
                    app_name='TestApp',
                    window_title='Test Window',
                    session_id='test-session',
                    is_correction=False,
                    pause_before=0.05,
                    typing_burst=True
                )
                for i in range(5)
            ]
            
            # Add events and flush
            for event in events:
                data_manager.add_keystroke(event)
            data_manager.flush_buffer()
            
            # Load events back
            loaded_events = data_manager.load_data()
            
            assert len(loaded_events) == 5
            assert loaded_events[0].key_char == 'A'
            assert loaded_events[-1].key_char == 'E'
    
    def test_buffer_auto_flush(self):
        """Test automatic buffer flushing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_manager = DataManager(temp_dir)
            data_manager._buffer_size = 3  # Small buffer for testing
            
            # Add events that should trigger auto-flush
            for i in range(5):
                event = KeystrokeEvent(
                    timestamp=1234567890.0 + i,
                    key_code=65,
                    key_char='A',
                    key_name='A',
                    dwell_time=0.1,
                    time_since_last=0.2,
                    app_name='TestApp',
                    window_title='Test Window',
                    session_id='test-session',
                    is_correction=False,
                    pause_before=0.05,
                    typing_burst=True
                )
                data_manager.add_keystroke(event)
            
            # Buffer should have been flushed automatically
            assert len(data_manager._buffer) == 2  # 5 - 3 (flushed)

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_finger_mapping(self):
        """Test finger assignment for keys."""
        assert get_finger_for_key('a') == 'left_pinky'
        assert get_finger_for_key('f') == 'left_index'
        assert get_finger_for_key('j') == 'right_index'
        assert get_finger_for_key('p') == 'right_pinky'
        assert get_finger_for_key(' ') == 'thumbs'
        assert get_finger_for_key('unknown') == 'unknown'
    
    def test_wpm_calculation(self):
        """Test words per minute calculation."""
        # Create events representing 25 characters (5 words)
        events = []
        for i in range(25):
            events.append(KeystrokeEvent(
                timestamp=1234567890.0,
                key_code=65,
                key_char='a',
                key_name='a',
                dwell_time=0.1,
                time_since_last=0.2,
                app_name='TestApp',
                window_title='Test Window',
                session_id='test-session',
                is_correction=False,
                pause_before=0.05,
                typing_burst=True
            ))
        
        # 5 words in 60 seconds = 5 WPM
        wpm = calculate_wpm(events, 60.0)
        assert wpm == 5.0
        
        # Test with zero duration
        assert calculate_wpm(events, 0.0) == 0.0
    
    def test_typing_burst_detection(self):
        """Test typing burst detection."""
        events = [
            KeystrokeEvent(
                timestamp=1234567890.0,
                key_code=65,
                key_char='a',
                key_name='a',
                dwell_time=0.1,
                time_since_last=0.0,  # First keystroke
                app_name='TestApp',
                window_title='Test Window',
                session_id='test-session',
                is_correction=False,
                pause_before=0.0,
                typing_burst=False
            ),
            KeystrokeEvent(
                timestamp=1234567890.1,
                key_code=66,
                key_char='b',
                key_name='b',
                dwell_time=0.1,
                time_since_last=0.1,  # Fast typing
                app_name='TestApp',
                window_title='Test Window',
                session_id='test-session',
                is_correction=False,
                pause_before=0.0,
                typing_burst=False
            ),
            KeystrokeEvent(
                timestamp=1234567890.6,
                key_code=67,
                key_char='c',
                key_name='c',
                dwell_time=0.1,
                time_since_last=0.5,  # Slow typing
                app_name='TestApp',
                window_title='Test Window',
                session_id='test-session',
                is_correction=False,
                pause_before=0.0,
                typing_burst=False
            )
        ]
        
        processed_events = detect_typing_burst(events, threshold=0.15)
        
        # First event should not be burst (no previous keystroke)
        assert processed_events[0].typing_burst is False
        
        # Second event should be burst (0.1s < 0.15s threshold)
        assert processed_events[1].typing_burst is True
        
        # Third event should not be burst (0.5s > 0.15s threshold)
        assert processed_events[2].typing_burst is False

if __name__ == '__main__':
    pytest.main([__file__])