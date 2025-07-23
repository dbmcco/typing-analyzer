# ABOUTME: Shared utilities for typing pattern analyzer
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import logging


@dataclass
class KeystrokeEvent:
    """Comprehensive keystroke event data structure."""

    timestamp: float
    key_code: int
    key_char: str
    key_name: str
    dwell_time: float
    time_since_last: float
    app_name: str
    window_title: str
    session_id: str
    is_correction: bool
    pause_before: float
    typing_burst: bool
    finger_assignment: Optional[str] = None
    cognitive_load_indicator: Optional[float] = None
    correction_type: Optional[str] = None
    corrected_text: Optional[str] = None
    likely_typo: Optional[bool] = None
    typo_pattern: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeystrokeEvent":
        """Create from dictionary."""
        return cls(**data)


# Standard QWERTY finger mapping for analysis
FINGER_MAP = {
    # Left hand
    "q": "left_pinky",
    "a": "left_pinky",
    "z": "left_pinky",
    "1": "left_pinky",
    "w": "left_ring",
    "s": "left_ring",
    "x": "left_ring",
    "2": "left_ring",
    "e": "left_middle",
    "d": "left_middle",
    "c": "left_middle",
    "3": "left_middle",
    "r": "left_index",
    "f": "left_index",
    "v": "left_index",
    "4": "left_index",
    "t": "left_index",
    "g": "left_index",
    "b": "left_index",
    "5": "left_index",
    # Right hand
    "y": "right_index",
    "h": "right_index",
    "n": "right_index",
    "6": "right_index",
    "u": "right_index",
    "j": "right_index",
    "m": "right_index",
    "7": "right_index",
    "i": "right_middle",
    "k": "right_middle",
    ",": "right_middle",
    "8": "right_middle",
    "o": "right_ring",
    "l": "right_ring",
    ".": "right_ring",
    "9": "right_ring",
    "p": "right_pinky",
    ";": "right_pinky",
    "/": "right_pinky",
    "0": "right_pinky",
    # Special keys
    " ": "thumbs",
    "shift": "pinky",
    "ctrl": "pinky",
    "cmd": "thumb",
    "alt": "thumb",
    "tab": "left_pinky",
    "caps": "left_pinky",
    "return": "right_pinky",
    "delete": "right_pinky",
    "backspace": "right_pinky",
}


class ConfigManager:
    """Configuration management with validation."""

    def __init__(self, config_path: Union[str, Path] = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and validate configuration."""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            logging.warning(f"Config file {self.config_path} not found, using defaults")
            return self._default_config()
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}")
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration values."""
        return {
            "collection": {
                "sample_rate_hz": 1000,
                "pause_thresholds": [0.5, 1.0, 2.0, 5.0],
                "buffer_size": 10000,
                "save_interval_seconds": 60,
            },
            "analysis": {
                "min_session_duration": 30,
                "hesitation_threshold": 0.8,
                "burst_threshold": 0.15,
                "flow_state_threshold": 60,
            },
            "output": {
                "data_directory": "./data",
                "reports_directory": "./reports",
                "log_level": "INFO",
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation."""
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class DataManager:
    """Efficient data storage and retrieval."""

    def __init__(self, data_dir: Union[str, Path] = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._buffer: List[KeystrokeEvent] = []
        self._buffer_size = 10000

    def add_keystroke(self, event: KeystrokeEvent) -> None:
        """Add keystroke to buffer."""
        self._buffer.append(event)
        if len(self._buffer) >= self._buffer_size:
            self.flush_buffer()

    def flush_buffer(self) -> None:
        """Save buffer to disk."""
        if not self._buffer:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"keystrokes_{timestamp}.json"

        data = [event.to_dict() for event in self._buffer]
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        logging.info(f"Saved {len(self._buffer)} keystrokes to {filename}")
        self._buffer.clear()

    def load_data(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[KeystrokeEvent]:
        """Load keystroke data within date range."""
        events = []
        for file_path in self.data_dir.glob("keystrokes_*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        event = KeystrokeEvent.from_dict(item)
                        if self._in_date_range(event.timestamp, start_date, end_date):
                            events.append(event)
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error loading {file_path}: {e}")

        return sorted(events, key=lambda x: x.timestamp)

    def _in_date_range(
        self, timestamp: float, start: Optional[datetime], end: Optional[datetime]
    ) -> bool:
        """Check if timestamp is within date range."""
        dt = datetime.fromtimestamp(timestamp)
        if start and dt < start:
            return False
        if end and dt > end:
            return False
        return True


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("typing_analyzer.log"), logging.StreamHandler()],
    )


def generate_session_id() -> str:
    """Generate unique session identifier."""
    return str(uuid.uuid4())


def get_finger_for_key(key: str) -> str:
    """Get finger assignment for a key."""
    return FINGER_MAP.get(key.lower(), "unknown")


def calculate_wpm(keystrokes: List[KeystrokeEvent], duration_seconds: float) -> float:
    """Calculate words per minute from keystroke data."""
    if duration_seconds <= 0:
        return 0.0

    # Count characters (excluding special keys)
    char_count = sum(
        1 for k in keystrokes if len(k.key_char) == 1 and k.key_char.isalnum()
    )

    # Standard WPM calculation (5 characters = 1 word)
    words = char_count / 5
    minutes = duration_seconds / 60

    return words / minutes if minutes > 0 else 0.0


def detect_typing_burst(
    events: List[KeystrokeEvent], threshold: float = 0.15
) -> List[KeystrokeEvent]:
    """Mark events that are part of typing bursts."""
    for i, event in enumerate(events):
        if i > 0 and event.time_since_last < threshold:
            event.typing_burst = True
        else:
            event.typing_burst = False
    return events
