# Advanced macOS Typing Pattern Analyzer

A sophisticated Python-based tool for deep analysis of typing behavior, efficiency patterns, and keyboard usage habits on macOS. Provides microsecond-precision keystroke capture with comprehensive behavioral insights and professional-grade analysis.

## 🚀 Quick Start

**Easy launcher script with automatic setup:**
```bash
# 6 minutes of typing analysis
./typing-analyzer.sh 0.1

# 30 minutes
./typing-analyzer.sh 0.5

# 2 hours
./typing-analyzer.sh 2
```

The script automatically:
- ✅ Creates virtual environment
- ✅ Installs dependencies  
- ✅ Captures keystrokes
- ✅ Generates analysis report
- ✅ Opens results in browser

## Features

### Data Collection
- **Microsecond-precision keystroke capture** with comprehensive timing analysis
- **Application context tracking** using macOS NSWorkspace integration
- **Complete content capture** including keystrokes, window titles, and app context
- **Advanced timing metrics** including dwell time, inter-keystroke intervals, and pause detection
- **Real-time cognitive load calculation** based on typing patterns and context

### Analysis Capabilities
- **Key Usage Analysis**: Character/key frequency, error patterns, correction analysis
- **Hesitation Pattern Detection**: Keys causing typing flow interruption and cognitive load
- **Efficiency Metrics**: WPM calculation, typing consistency, flow state detection
- **Finger Usage Analysis**: Load distribution, hand balance, same-finger bigram detection
- **Cognitive Load Assessment**: Context-aware mental processing indicators
- **Behavioral Pattern Recognition**: Burst typing, rhythm analysis, productivity correlations

### Reporting & Visualization
- **Interactive HTML reports** with comprehensive statistics and insights
- **CSV data export** for external analysis and research
- **JSON structured output** for API integration and further processing
- **Statistical analysis** with percentiles, distributions, and correlation metrics
- **Time-series visualization** for performance trends and pattern recognition

## Installation

### Prerequisites
- macOS 10.14+ (Mojave or later)
- Python 3.9+
- Accessibility permissions for keylogging

### Setup Instructions

**Option 1: Automatic Setup (Recommended)**
1. Navigate to project directory
2. Run: `./typing-analyzer.sh 0.1` 
3. Script handles virtual environment and dependencies automatically
4. Grant accessibility permissions when prompted

**Option 2: Manual Setup**
1. **Clone and navigate to the project:**
   ```bash
   cd /Users/braydon/projects/experiments/typing-analyzer
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Grant Accessibility Permissions:**
   - System Preferences → Security & Privacy → Privacy → Accessibility
   - Add Terminal (or your terminal app) to the list
   - Enable the checkbox for your terminal application

## Usage

### Easy Launch Script (Recommended)

```bash
# Quick 6-minute session
./typing-analyzer.sh 0.1

# Standard 30-minute session  
./typing-analyzer.sh 0.5

# Extended 2-hour session
./typing-analyzer.sh 2

# Run until manually stopped (Ctrl+C)
./typing-analyzer.sh
```

### Manual Usage

**Data Collection:**
```bash
# Activate virtual environment first
source venv/bin/activate

# Start keystroke monitoring
python3 src/keylogger.py

# Run for specific duration
python3 src/keylogger.py --duration 2h

# Use custom configuration
python3 src/keylogger.py --config custom_config.yaml
```

**Data Analysis:**
```bash
# Run comprehensive analysis
python3 src/analyzer.py

# Generate specific report types
python3 src/analyzer.py --report-type summary
python3 src/analyzer.py --export-csv --visualizations

# Export to specific directory
python3 src/analyzer.py --output ./my_reports/
```

### Configuration

Customize behavior via `config.yaml`:

```yaml
collection:
  sample_rate_hz: 1000          # Keystroke sampling rate
  pause_thresholds: [0.5, 1.0, 2.0, 5.0]  # Pause detection levels
  save_interval_seconds: 60     # Auto-save frequency

analysis:
  hesitation_threshold: 0.8     # Pause duration indicating hesitation
  burst_threshold: 0.15         # Max interval for burst typing
  flow_state_threshold: 60      # Min keystrokes for flow state

privacy:
  capture_all_content: true     # Full keystroke capture
  store_passwords: true         # Include password fields
  full_context_tracking: true   # Window titles and app context
```

## Analysis Outputs

### Key Usage Report
- Character and key frequency distributions
- Most/least used keys with percentages
- Error rates and correction patterns
- Special key usage analysis

### Hesitation Analysis
- Keys causing typing interruptions
- Context-specific pause patterns
- Cognitive load indicators by application
- Hunt-and-peck detection metrics

### Efficiency Metrics
- Words per minute (overall and per-application)
- Typing consistency scores
- Flow state detection and duration
- Burst typing analysis
- Keystroke efficiency ratios

### Finger Usage Analysis
- Per-finger keystroke distribution
- Hand balance metrics (left/right/thumb usage)
- Same-finger bigram detection (inefficient sequences)
- Finger strength vs. usage correlation

### Cognitive Load Assessment
- Mental processing indicators from pause patterns
- Context-switching overhead analysis
- App-specific cognitive requirements
- Time-of-day cognitive load patterns

## Architecture

```
src/
├── keylogger.py      # Core data collection with macOS integration
├── analyzer.py       # Comprehensive analysis engine
└── utils.py          # Shared utilities and data structures

data/                 # Keystroke data storage (JSON format)
reports/              # Generated analysis reports
config.yaml           # Configuration settings
```

### Key Components

- **MacOSAppTracker**: Real-time application and window context monitoring
- **TypingAnalyzerKeylogger**: High-precision keystroke capture with accessibility integration
- **TypingPatternAnalyzer**: Statistical analysis engine with behavioral insights
- **DataManager**: Efficient data persistence and retrieval
- **ConfigManager**: Flexible configuration management with validation

## Data Structure

Each keystroke event contains:
```python
{
    'timestamp': float,              # Microsecond precision
    'key_code': int,                # Raw key identifier
    'key_char': str,                # Character representation
    'key_name': str,                # Human-readable key name
    'dwell_time': float,            # Key hold duration
    'time_since_last': float,       # Inter-keystroke interval
    'app_name': str,                # Active application
    'window_title': str,            # Window context
    'session_id': str,              # Unique session ID
    'is_correction': bool,          # Correction keystroke flag
    'pause_before': float,          # Pre-keystroke pause
    'typing_burst': bool,           # Rapid typing indicator
    'finger_assignment': str,       # Finger mapping
    'cognitive_load_indicator': float  # Mental processing metric
}
```

## Performance

- **CPU Usage**: <1% during collection
- **Memory Footprint**: <100MB with 10K keystroke buffer
- **Storage**: ~1KB per minute of typing
- **Analysis Speed**: <500ms for typical daily sessions

## Privacy & Security

This tool captures comprehensive typing data including:
- All keystrokes and characters typed
- Application context and window titles
- Timing patterns and behavioral metrics

**Data is stored locally** in JSON format. No network transmission occurs.

For privacy-conscious usage, modify `config.yaml`:
```yaml
privacy:
  capture_all_content: false     # Skip sensitive applications
  store_passwords: false         # Exclude password fields
  full_context_tracking: false   # Limit context capture
```

## Research Applications

Suitable for:
- **Typing efficiency research** and keyboard layout optimization
- **Cognitive load assessment** in human-computer interaction studies
- **Productivity analysis** and workflow optimization
- **Accessibility research** for adaptive input systems
- **Behavioral pattern recognition** in user interface design

## Troubleshooting

### Common Issues

**"Permission denied" errors:**
- Ensure Accessibility permissions are granted
- Run from terminal that has accessibility access

**No data captured:**
- Check `data/` directory exists and is writable
- Verify configuration file syntax
- Check system logs for error messages

**Analysis fails:**
- Ensure sufficient data exists (minimum 100 keystrokes)
- Check for corrupted JSON files in data directory
- Verify all dependencies are installed

### Logging

Enable detailed logging:
```yaml
output:
  log_level: DEBUG
```

Logs are written to `typing_analyzer.log` and console.

## Development

### Testing
```bash
pytest tests/ -v --cov=src
```

### Code Quality
```bash
black src/
flake8 src/
mypy src/
```

### Contributing

1. Follow TDD principles with >90% test coverage
2. Use type hints throughout
3. Maintain <500ms analysis response times
4. Document all public functions and classes

## License

MIT License - See LICENSE file for details.

## Support

For issues and feature requests, create an issue in the project repository.