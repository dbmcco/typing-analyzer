# ABOUTME: Core keylogger implementation with macOS accessibility integration and comprehensive data collection
import time
import threading
import signal
import sys
import logging
from typing import Optional, Dict, Any, List

# macOS specific imports
from pynput import keyboard
from Cocoa import NSWorkspace

# Local imports
try:
    from .utils import (
        KeystrokeEvent,
        ConfigManager,
        DataManager,
        setup_logging,
        generate_session_id,
        get_finger_for_key,
    )
except ImportError:
    from utils import (  # type: ignore
        KeystrokeEvent,
        ConfigManager,
        DataManager,
        setup_logging,
        generate_session_id,
        get_finger_for_key,
    )


class MacOSAppTracker:
    """Track active applications and window context on macOS."""

    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.current_app = ""
        self.current_window = ""

    def get_active_app(self) -> str:
        """Get the currently active application name."""
        try:
            active_app = self.workspace.frontmostApplication()
            if active_app:
                return active_app.localizedName() or "Unknown"
        except Exception as e:
            logging.error(f"Error getting active app: {e}")
        return "Unknown"

    def get_window_title(self) -> str:
        """Get the current window title using Accessibility API."""
        try:
            from Cocoa import (
                AXUIElementCreateApplication,
                AXUIElementCopyAttributeValue,
                kAXFocusedWindowAttribute,
                kAXTitleAttribute,
            )

            # Get frontmost application
            app = self.workspace.frontmostApplication()
            if not app:
                return ""

            pid = app.processIdentifier()
            app_ref = AXUIElementCreateApplication(pid)

            # Get focused window
            window_ref = AXUIElementCopyAttributeValue(
                app_ref, kAXFocusedWindowAttribute, None
            )[1]
            if not window_ref:
                return ""

            # Get window title
            title = AXUIElementCopyAttributeValue(window_ref, kAXTitleAttribute, None)[
                1
            ]
            return title or ""

        except Exception as e:
            logging.debug(f"Could not get window title: {e}")
            return ""


class TypingAnalyzerKeylogger:
    """Advanced keylogger with comprehensive typing pattern analysis."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigManager(config_path or "config.yaml")
        self.data_manager = DataManager(
            self.config.get("output.data_directory", "./data")
        )
        self.app_tracker = MacOSAppTracker()

        # State tracking
        self.session_id = generate_session_id()
        self.last_keystroke_time = 0.0
        self.is_running = False
        self.key_press_times: Dict[int, float] = {}

        # Statistics
        self.total_keystrokes = 0
        self.session_start_time = time.time()
        
        # Enhanced error tracking
        self.recent_keystrokes: List[str] = []  # Last 10 keystrokes for context
        self.correction_sequences: List[Dict[str, Any]] = []
        self.last_key_was_correction = False

        # Setup logging
        setup_logging(self.config.get("output.log_level", "INFO"))

        logging.info(f"Initialized typing analyzer with session ID: {self.session_id}")

    def _calculate_cognitive_load(self, pause_duration: float, context: str) -> float:
        """Calculate cognitive load indicator based on pause patterns."""
        # Baseline cognitive load calculation
        base_load = min(pause_duration / 2.0, 1.0)  # Normalize to 0-1

        # Context-specific adjustments
        if "code" in context.lower() or "terminal" in context.lower():
            base_load *= 1.2  # Code requires more thinking
        elif "email" in context.lower() or "message" in context.lower():
            base_load *= 0.8  # Casual writing is easier

        return min(base_load, 1.0)

    def _is_correction_key(self, key: Any) -> bool:
        """Check if key is a correction/deletion key."""
        if hasattr(key, "name"):
            return key.name in ["backspace", "delete"]
        return False
    
    def _detect_correction_sequence(self, key_char: str, key_name: str, is_correction: bool) -> Dict[str, Any]:
        """Detect and analyze correction sequences and typo patterns."""
        correction_data = {
            'is_correction': is_correction,
            'correction_length': 0,
            'corrected_text': '',
            'likely_typo': False,
            'correction_type': 'none'
        }
        
        if is_correction:
            # Track correction sequence
            if not self.last_key_was_correction:
                # Start of new correction sequence
                correction_data['correction_type'] = 'single_correction'
            else:
                # Continuing correction sequence
                correction_data['correction_type'] = 'multi_correction'
                
            # Estimate what was corrected based on recent keystrokes
            if len(self.recent_keystrokes) > 0:
                correction_data['corrected_text'] = self.recent_keystrokes[-1] if self.recent_keystrokes else ''
                correction_data['correction_length'] = 1
                
                # Remove from recent keystrokes as it's being corrected
                self.recent_keystrokes = self.recent_keystrokes[:-1]
        else:
            # Regular keystroke
            if key_char and key_char.isprintable():
                # Add to recent keystrokes buffer (keep last 10)
                self.recent_keystrokes.append(key_char)
                if len(self.recent_keystrokes) > 10:
                    self.recent_keystrokes.pop(0)
                
                # Check for likely typos based on patterns
                if len(self.recent_keystrokes) >= 2:
                    # Look for common typo patterns
                    last_two = ''.join(self.recent_keystrokes[-2:])
                    
                    # Common typo patterns
                    common_typos = {
                        'teh': 'the', 'adn': 'and', 'recieve': 'receive',
                        'seperate': 'separate', 'definately': 'definitely',
                        'occured': 'occurred', 'accomodate': 'accommodate'
                    }
                    
                    # Check if recent text contains common typos
                    recent_text = ''.join(self.recent_keystrokes[-6:]).lower()
                    for typo, correct in common_typos.items():
                        if typo in recent_text:
                            correction_data['likely_typo'] = True
                            correction_data['typo_pattern'] = f"{typo} -> {correct}"
                            break
        
        self.last_key_was_correction = is_correction
        return correction_data

    def _get_key_info(self, key: Any) -> tuple[int, str, str]:
        """Extract key information from pynput key object."""
        try:
            if hasattr(key, "char") and key.char:
                # Regular character key
                return hash(key.char), key.char, key.char
            elif hasattr(key, "name"):
                # Special key
                key_code = hash(key.name)
                return key_code, "", key.name
            else:
                # Fallback
                return hash(str(key)), "", str(key)
        except AttributeError:
            return hash(str(key)), "", str(key)

    def on_key_press(self, key: Any) -> None:
        """Handle key press events with comprehensive data collection."""
        try:
            current_time = time.time()
            key_code, key_char, key_name = self._get_key_info(key)

            # Store press time for dwell calculation
            self.key_press_times[key_code] = current_time

        except Exception as e:
            logging.error(f"Error in key press handler: {e}")

    def on_key_release(self, key: Any) -> None:
        """Handle key release events and create keystroke records."""
        try:
            current_time = time.time()
            key_code, key_char, key_name = self._get_key_info(key)

            # Calculate dwell time
            press_time = self.key_press_times.get(key_code, current_time)
            dwell_time = current_time - press_time

            # Calculate time since last keystroke
            time_since_last = (
                current_time - self.last_keystroke_time
                if self.last_keystroke_time > 0
                else 0.0
            )

            # Get application context
            app_name = self.app_tracker.get_active_app()
            window_title = self.app_tracker.get_window_title()

            # Detect corrections and pauses
            is_correction = self._is_correction_key(key)
            pause_before = time_since_last if time_since_last > 0.1 else 0.0
            
            # Enhanced correction analysis
            correction_data = self._detect_correction_sequence(key_char, key_name, is_correction)

            # Calculate cognitive load
            cognitive_load = self._calculate_cognitive_load(
                pause_before, f"{app_name} {window_title}"
            )

            # Create keystroke event
            event = KeystrokeEvent(
                timestamp=current_time,
                key_code=key_code,
                key_char=key_char,
                key_name=key_name,
                dwell_time=dwell_time,
                time_since_last=time_since_last,
                app_name=app_name,
                window_title=window_title,
                session_id=self.session_id,
                is_correction=is_correction,
                pause_before=pause_before,
                typing_burst=time_since_last
                < self.config.get("analysis.burst_threshold", 0.15),
                finger_assignment=get_finger_for_key(key_char or key_name),
                cognitive_load_indicator=cognitive_load,
                correction_type=correction_data.get('correction_type'),
                corrected_text=correction_data.get('corrected_text'),
                likely_typo=correction_data.get('likely_typo'),
                typo_pattern=correction_data.get('typo_pattern'),
            )

            # Store the event
            self.data_manager.add_keystroke(event)

            # Update tracking variables
            self.last_keystroke_time = current_time
            self.total_keystrokes += 1

            # Clean up press time tracking
            if key_code in self.key_press_times:
                del self.key_press_times[key_code]

            # Log progress periodically
            if self.total_keystrokes % 1000 == 0:
                elapsed = current_time - self.session_start_time
                logging.info(
                    f"Recorded {self.total_keystrokes} keystrokes in {elapsed:.1f}s"
                )

        except Exception as e:
            logging.error(f"Error in key release handler: {e}")

    def start_monitoring(self) -> None:
        """Start the keylogger monitoring."""
        if self.is_running:
            logging.warning("Keylogger is already running")
            return

        self.is_running = True
        self.session_start_time = time.time()

        logging.info("Starting typing pattern monitoring...")
        logging.info("Press Ctrl+C to stop monitoring and save data")

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Setup periodic buffer flush
        flush_timer = threading.Timer(
            self.config.get("collection.save_interval_seconds", 60),
            self._periodic_flush,
        )
        flush_timer.daemon = True
        flush_timer.start()

        # Start keyboard monitoring with proper signal handling
        try:
            self.listener = keyboard.Listener(
                on_press=self.on_key_press, on_release=self.on_key_release
            )
            self.listener.start()
            
            # Keep main thread alive and responsive to signals
            while self.is_running:
                try:
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    logging.info("Keyboard interrupt received")
                    break
            
            self.listener.stop()
            
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt during startup")
            self.stop_monitoring()
        except Exception as e:
            logging.error(f"Error starting keyboard listener: {e}")
            self.stop_monitoring()

    def _periodic_flush(self) -> None:
        """Periodically flush data buffer."""
        if self.is_running:
            self.data_manager.flush_buffer()
            # Schedule next flush
            flush_timer = threading.Timer(
                self.config.get("collection.save_interval_seconds", 60),
                self._periodic_flush,
            )
            flush_timer.daemon = True
            flush_timer.start()

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals gracefully."""
        logging.info(f"Received signal {signum}, shutting down...")
        self.is_running = False
        if hasattr(self, 'listener'):
            self.listener.stop()
        self.stop_monitoring()

    def stop_monitoring(self) -> None:
        """Stop monitoring and save remaining data."""
        if not self.is_running:
            return

        self.is_running = False

        # Flush remaining data
        self.data_manager.flush_buffer()

        # Log session summary
        elapsed = time.time() - self.session_start_time
        logging.info(
            f"Session completed: {self.total_keystrokes} keystrokes in {elapsed:.1f}s"
        )
        logging.info(
            f"Average rate: {self.total_keystrokes/elapsed:.1f} keystrokes/second"
        )

        sys.exit(0)


def main():
    """Main entry point for the keylogger."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Advanced macOS Typing Pattern Analyzer"
    )
    parser.add_argument(
        "--config", default="config.yaml", help="Path to configuration file"
    )
    parser.add_argument(
        "--duration", type=str, help="Duration to run (e.g., '1h', '30m', '24h')"
    )

    args = parser.parse_args()

    # Check for accessibility permissions
    try:
        from Cocoa import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt

        trusted = AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
        if not trusted:
            print(
                "Please grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility"
            )
            sys.exit(1)
    except ImportError:
        logging.warning("Could not check accessibility permissions")

    # Initialize and start keylogger
    keylogger = TypingAnalyzerKeylogger(args.config)

    # Handle duration argument
    if args.duration:
        duration_seconds = parse_duration(args.duration)
        timer = threading.Timer(duration_seconds, keylogger.stop_monitoring)
        timer.start()
        logging.info(f"Will run for {args.duration} ({duration_seconds}s)")

    try:
        keylogger.start_monitoring()
    except KeyboardInterrupt:
        keylogger.stop_monitoring()


def parse_duration(duration_str: str) -> float:
    """Parse duration string like '1h', '30m', '24h' into seconds."""
    import re

    match = re.match(r"^(\d+)([hms])$", duration_str.lower())
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")

    value, unit = match.groups()
    value = int(value)

    if unit == "s":
        return value
    elif unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600
    else:
        raise ValueError(f"Invalid duration unit: {unit}")


if __name__ == "__main__":
    main()
