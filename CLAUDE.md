# Typing Pattern Analyzer - Claude Memory

## Project Overview
A comprehensive Python-based typing pattern analyzer for macOS that performs deep analysis of typing behavior, efficiency patterns, and keyboard usage habits. Production-ready tool with sophisticated data collection and behavioral insights.

## Key Features Implemented
- **Microsecond-precision keystroke capture** with comprehensive timing analysis
- **macOS accessibility integration** using NSWorkspace and pynput
- **Real-time cognitive load calculation** based on typing patterns and context
- **Advanced behavioral analysis**: hesitation detection, flow states, finger usage
- **Multi-format reporting**: Interactive HTML, JSON data export, CSV for research
- **Comprehensive CLI interface** with bash launcher script

## Architecture
```
typing-analyzer/
├── src/
│   ├── keylogger.py         # Core data collection with macOS integration
│   ├── analyzer.py          # Statistical analysis engine
│   ├── utils.py             # Data structures and utilities
│   └── __init__.py          # Package initialization
├── tests/                   # Comprehensive test suite (19 tests, 61% coverage)
├── data/                    # Keystroke data storage (JSON format)
├── reports/                 # Generated analysis reports
├── typing-analyzer.sh       # Main launcher script
├── config.yaml              # Configuration settings
└── requirements.txt         # Python dependencies
```

## Data Structure
Each keystroke event captures:
- Microsecond timestamp precision
- Key identification and character mapping
- Dwell time and inter-keystroke intervals
- Application context (NSWorkspace integration)
- Behavioral indicators (corrections, pauses, bursts)
- Finger assignments and cognitive load metrics
- Enhanced error tracking (correction_type, corrected_text, likely_typo, typo_pattern)

## Analysis Capabilities
1. **Key Usage Patterns**: Character/key frequency, error rates, correction analysis
2. **Enhanced Error Detection**: Multi-keystroke correction sequences, typo pattern recognition, context-aware mistake detection
3. **Hesitation Detection**: Keys causing typing flow interruption, context-aware pauses
4. **Efficiency Metrics**: WPM calculation, typing consistency, flow state detection
5. **Finger Usage Analysis**: Load distribution, hand balance, same-finger bigrams
6. **Cognitive Load Assessment**: Context-aware mental processing indicators
7. **Behavioral Recognition**: Burst typing, rhythm analysis, productivity correlations
8. **Word & Phrase Analysis**: Frequency patterns, optimization opportunities, vocabulary analysis
9. **Correction Analytics**: Error-prone characters, app-specific error rates, correction efficiency

## Usage
**Quick Start:**
```bash
# 6 minutes (0.1 hours)
./typing-analyzer.sh 0.1

# 30 minutes
./typing-analyzer.sh 0.5

# 2 hours
./typing-analyzer.sh 2
```

**CLI Tools:**
```bash
# Manual keylogger
python3 src/keylogger.py --duration 1h

# Analysis only
python3 src/analyzer.py
```

## Technical Implementation
- **Language**: Python 3.9+ with comprehensive type hints
- **Dependencies**: pynput, PyYAML, pandas, numpy, matplotlib, plotly
- **Platform**: macOS 10.14+ with accessibility permissions
- **Performance**: <1% CPU usage, <100MB memory footprint
- **Storage**: ~1KB per minute of typing data

## Quality Standards Met
- **Test Coverage**: 19/19 tests pass, 61% coverage
- **Code Quality**: Black formatting, flake8 compliance (minor line length exceptions)
- **Type Safety**: MyPy compatibility with comprehensive annotations
- **Documentation**: Complete docstrings, inline comments, usage examples

## Key Insights Provided
- **Typing Speed**: Overall and app-specific WPM with consistency metrics
- **Error Analysis**: Comprehensive mistake detection, typo patterns, correction efficiency
- **Efficiency Analysis**: Keystroke efficiency ratios, correction patterns
- **Behavioral Patterns**: Flow states, cognitive load by context, hesitation analysis
- **Ergonomic Data**: Finger usage distribution, hand balance, optimization suggestions
- **Productivity Metrics**: Peak performance periods, context switching overhead
- **Optimization Opportunities**: Text shortcuts, phrase shortcuts, hand balance improvements

## Recent Updates (Latest: Error Detection Enhancement)
- **Enhanced Error Detection System**: Comprehensive correction tracking and typo pattern analysis
  - Multi-keystroke correction sequence detection and analysis
  - Common typo pattern recognition ("teh" → "the", "adn" → "and", etc.)
  - Context-aware error detection using recent keystroke buffer
  - App-specific and time-based error rate analysis
  - Character-specific error analysis (which keys lead to corrections)
  - Correction efficiency metrics and sequence length tracking
- **Improved Signal Handling**: Fixed Ctrl+C not working issue with responsive loop design
- **Comprehensive HTML Reports**: Added dedicated error analysis section with tables
- **Enhanced Data Structure**: Added correction_type, corrected_text, likely_typo, typo_pattern fields
- **Console Error Insights**: Error statistics in analysis summary output
- **CSV Export Enhancement**: All error fields included for research analysis
- **Bash Launcher**: Automated virtual environment management
- **Duration Parsing**: Flexible time specification (decimals supported)
- **Error Handling**: Comprehensive accessibility permission management
- **Report Generation**: Automatic browser opening of analysis results
- **Code Cleanup**: Professional quality standards with proper formatting

## Configuration
Customizable via `config.yaml`:
- Sampling rates and buffer sizes
- Analysis thresholds and algorithms
- Privacy settings (full capture enabled by default)
- Output formats and directory preferences

## Privacy & Security
- **Local Processing**: All data remains on local machine
- **Full Capture**: Comprehensive keystroke and context logging
- **macOS Integration**: Proper accessibility API usage
- **User Control**: Easy start/stop with Ctrl+C

## Quality Gates
- `pytest` - All tests must pass (19/19 passing)
- `flake8` - Code style compliance (minor line length exceptions)
- `mypy` - Type checking (improved with annotations)
- `black` - Code formatting (applied consistently)

## Development Standards
- TDD approach with comprehensive test coverage
- Type-safe Python with strict mypy compliance
- Performance targets: <500ms analysis response times
- Professional code quality with automated formatting
- Comprehensive error handling and graceful degradation