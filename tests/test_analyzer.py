# ABOUTME: Unit tests for typing pattern analysis functionality
import pytest
import tempfile
from datetime import datetime
from pathlib import Path

from src.analyzer import TypingPatternAnalyzer
from src.utils import KeystrokeEvent, DataManager

class TestTypingPatternAnalyzer:
    """Test typing pattern analysis functionality."""
    
    @pytest.fixture
    def sample_events(self):
        """Create sample keystroke events for testing."""
        base_time = 1234567890.0
        return [
            KeystrokeEvent(
                timestamp=base_time + i * 0.2,
                key_code=65 + (i % 26),
                key_char=chr(65 + (i % 26)).lower(),
                key_name=chr(65 + (i % 26)).lower(),
                dwell_time=0.1,
                time_since_last=0.2 if i > 0 else 0.0,
                app_name='TextEdit' if i < 50 else 'Terminal',
                window_title='Document.txt' if i < 50 else 'Terminal Window',
                session_id='test-session',
                is_correction=(i % 10 == 9),  # Every 10th keystroke is correction
                pause_before=0.1 if i % 5 == 0 else 0.05,  # Varying pauses
                typing_burst=(i % 3 != 0),  # Most are burst typing
                finger_assignment='left_pinky' if chr(65 + (i % 26)).lower() in 'qaz' else 'right_index',
                cognitive_load_indicator=0.3 + (i % 10) * 0.07  # Varying cognitive load
            )
            for i in range(100)
        ]
    
    @pytest.fixture
    def analyzer_with_data(self, sample_events):
        """Create analyzer with sample data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create temporary config
            config_content = f"""
output:
  data_directory: {temp_dir}/data
  reports_directory: {temp_dir}/reports
analysis:
  hesitation_threshold: 0.8
  burst_threshold: 0.15
            """
            
            config_path = Path(temp_dir) / 'config.yaml'
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            analyzer = TypingPatternAnalyzer(str(config_path))
            analyzer.events = sample_events
            
            yield analyzer
    
    def test_key_usage_analysis(self, analyzer_with_data):
        """Test key usage pattern analysis."""
        results = analyzer_with_data.analyze_key_usage()
        
        assert 'character_frequencies' in results
        assert 'key_frequencies' in results
        assert 'total_keystrokes' in results
        assert 'correction_counts' in results
        
        # Should have 100 total keystrokes
        assert results['total_keystrokes'] == 100
        
        # Should have corrections (every 10th keystroke)
        assert results['total_corrections'] == 10
        
        # Should have frequency data
        assert len(results['character_frequencies']) > 0
        assert len(results['most_frequent_chars']) > 0
    
    def test_hesitation_analysis(self, analyzer_with_data):
        """Test hesitation pattern analysis."""
        results = analyzer_with_data.analyze_hesitation_patterns()
        
        assert 'key_hesitation_stats' in results
        assert 'pause_distribution' in results
        assert 'total_pauses' in results
        
        # Should detect pauses
        assert results['total_pauses'] > 0
        
        # Should have pause distribution stats
        assert 'mean' in results['pause_distribution']
        assert 'median' in results['pause_distribution']
        assert 'percentiles' in results['pause_distribution']
    
    def test_efficiency_metrics(self, analyzer_with_data):
        """Test efficiency metrics calculation."""
        results = analyzer_with_data.analyze_efficiency_metrics()
        
        assert 'overall_wpm' in results
        assert 'session_duration_minutes' in results
        assert 'efficiency_ratio' in results
        assert 'burst_typing_percentage' in results
        
        # Should calculate valid WPM
        assert results['overall_wpm'] >= 0
        
        # Should have reasonable efficiency ratio (90% since 10% are corrections)
        assert 85 <= results['efficiency_ratio'] <= 95
        
        # Should detect burst typing
        assert results['burst_typing_percentage'] > 0
    
    def test_finger_usage_analysis(self, analyzer_with_data):
        """Test finger usage analysis."""
        results = analyzer_with_data.analyze_finger_usage()
        
        assert 'finger_usage_counts' in results
        assert 'finger_usage_percentages' in results
        assert 'hand_balance' in results
        assert 'most_used_finger' in results
        
        # Should have finger usage data
        assert len(results['finger_usage_counts']) > 0
        
        # Should have hand balance data
        assert 'left' in results['hand_balance']
        assert 'right' in results['hand_balance']
        
        # Should identify most used finger
        assert results['most_used_finger'] is not None
    
    def test_cognitive_load_analysis(self, analyzer_with_data):
        """Test cognitive load analysis."""
        results = analyzer_with_data.analyze_cognitive_load()
        
        assert 'overall_cognitive_load' in results
        assert 'app_cognitive_load' in results
        assert 'high_load_events' in results
        
        # Should calculate cognitive load
        assert 0 <= results['overall_cognitive_load'] <= 1
        
        # Should have app-specific data
        assert len(results['app_cognitive_load']) > 0
    
    def test_flow_state_detection(self, analyzer_with_data):
        """Test flow state detection."""
        # Create events with sustained fast typing
        flow_events = []
        base_time = 1234567890.0
        
        for i in range(100):
            event = KeystrokeEvent(
                timestamp=base_time + i * 0.1,  # Fast consistent typing
                key_code=65 + (i % 26),
                key_char=chr(65 + (i % 26)).lower(),
                key_name=chr(65 + (i % 26)).lower(),
                dwell_time=0.08,
                time_since_last=0.1,
                app_name='TextEdit',
                window_title='Document.txt',
                session_id='test-session',
                is_correction=False,  # No corrections in flow
                pause_before=0.02,    # Minimal pauses
                typing_burst=True,    # All burst typing
                finger_assignment='left_index'
            )
            flow_events.append(event)
        
        analyzer_with_data.events = flow_events
        flow_periods = analyzer_with_data._detect_flow_states(min_keystrokes=50)
        
        # Should detect at least one flow period
        assert len(flow_periods) > 0
        
        # Flow period should have expected properties
        flow = flow_periods[0]
        assert 'duration_seconds' in flow
        assert 'keystroke_count' in flow
        assert 'wpm' in flow
        assert flow['keystroke_count'] >= 50
    
    def test_full_analysis(self, analyzer_with_data):
        """Test comprehensive analysis."""
        results = analyzer_with_data.run_full_analysis()
        
        # Should have all major analysis sections
        expected_sections = [
            'metadata',
            'key_usage',
            'hesitation_patterns', 
            'efficiency_metrics',
            'finger_usage',
            'cognitive_load'
        ]
        
        for section in expected_sections:
            assert section in results
        
        # Metadata should have basic info
        assert 'total_events' in results['metadata']
        assert results['metadata']['total_events'] == 100
        
        # Should have timestamp
        assert 'analysis_timestamp' in results['metadata']
    
    def test_report_generation(self, analyzer_with_data):
        """Test report generation in different formats."""
        # Run analysis first
        analyzer_with_data.run_full_analysis()
        
        # Generate reports
        generated_files = analyzer_with_data.generate_reports(['json', 'html', 'csv'])
        
        # Should generate all requested formats
        assert 'json' in generated_files
        assert 'html' in generated_files
        assert 'csv' in generated_files
        
        # Files should exist
        for file_path in generated_files.values():
            assert Path(file_path).exists()
            assert Path(file_path).stat().st_size > 0
    
    def test_empty_data_handling(self):
        """Test handling of empty dataset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_content = f"""
output:
  data_directory: {temp_dir}/data
  reports_directory: {temp_dir}/reports
            """
            
            config_path = Path(temp_dir) / 'config.yaml'
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            analyzer = TypingPatternAnalyzer(str(config_path))
            # Empty events list
            analyzer.events = []
            
            # Should handle empty data gracefully
            results = analyzer.run_full_analysis()
            assert results == {}
    
    def test_insufficient_data_handling(self, analyzer_with_data):
        """Test handling of insufficient data for certain analyses."""
        # Reduce to very small dataset
        analyzer_with_data.events = analyzer_with_data.events[:5]
        
        results = analyzer_with_data.run_full_analysis()
        
        # Should still have basic structure but may have limited analysis
        assert 'metadata' in results
        assert results['metadata']['total_events'] == 5

if __name__ == '__main__':
    pytest.main([__file__])