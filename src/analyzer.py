# ABOUTME: Analysis engine for typing patterns with statistical insights
import json
import statistics
from collections import defaultdict, Counter
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import re

import pandas as pd
import numpy as np

try:
    from .utils import (
        KeystrokeEvent,
        ConfigManager,
        DataManager,
        setup_logging,
        calculate_wpm,
    )
except ImportError:
    from utils import (  # type: ignore
        KeystrokeEvent,
        ConfigManager,
        DataManager,
        setup_logging,
        calculate_wpm,
    )


class TypingPatternAnalyzer:
    """Advanced typing pattern analysis with comprehensive behavioral insights."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = ConfigManager(config_path or "config.yaml")
        self.data_manager = DataManager(
            self.config.get("output.data_directory", "./data")
        )
        self.reports_dir = Path(
            self.config.get("output.reports_directory", "./reports")
        )
        self.reports_dir.mkdir(exist_ok=True)

        setup_logging(self.config.get("output.log_level", "INFO"))

        self.events: List[KeystrokeEvent] = []
        self.analysis_results: Dict[str, Any] = {}

    def load_data(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> None:
        """Load keystroke data for analysis."""
        logging.info("Loading keystroke data...")
        self.events = self.data_manager.load_data(start_date, end_date)
        logging.info(f"Loaded {len(self.events)} keystroke events")

    def analyze_key_usage(self) -> Dict[str, Any]:
        """Analyze key usage patterns and frequencies."""
        logging.info("Analyzing key usage patterns...")

        # Character frequency analysis
        char_counts: Counter[str] = Counter()
        key_counts: Counter[str] = Counter()
        correction_counts: Counter[str] = Counter()

        for event in self.events:
            if event.key_char:
                char_counts[event.key_char] += 1
            key_counts[event.key_name] += 1
            if event.is_correction:
                correction_counts[event.key_name] += 1

        # Calculate percentages
        total_keys = len(self.events)
        char_frequencies = {
            char: (count / total_keys) * 100
            for char, count in char_counts.most_common()
        }
        key_frequencies = {
            key: (count / total_keys) * 100 for key, count in key_counts.most_common()
        }

        # Error rates
        error_rates = {}
        for key, corrections in correction_counts.items():
            total_uses = key_counts.get(key, 0)
            if total_uses > 0:
                error_rates[key] = (corrections / total_uses) * 100

        return {
            "character_frequencies": char_frequencies,
            "key_frequencies": key_frequencies,
            "most_frequent_chars": list(char_counts.most_common(10)),
            "least_frequent_chars": list(char_counts.most_common()[-10:]),
            "correction_counts": dict(correction_counts),
            "error_rates": error_rates,
            "total_keystrokes": total_keys,
            "total_corrections": sum(correction_counts.values()),
        }

    def analyze_hesitation_patterns(self) -> Dict[str, Any]:
        """Analyze typing hesitations and pause patterns."""
        logging.info("Analyzing hesitation patterns...")

        pause_threshold = self.config.get("analysis.hesitation_threshold", 0.8)

        # Collect pause data
        key_pauses = defaultdict(list)
        app_pauses = defaultdict(list)
        context_pauses = defaultdict(list)

        for event in self.events:
            if event.pause_before > 0:
                key_pauses[event.key_char or event.key_name].append(event.pause_before)
                app_pauses[event.app_name].append(event.pause_before)
                context_pauses[f"{event.app_name}:{event.window_title}"].append(
                    event.pause_before
                )

        # Calculate hesitation metrics
        key_hesitation_stats = {}
        for key, pauses in key_pauses.items():
            if len(pauses) > 5:  # Minimum sample size
                key_hesitation_stats[key] = {
                    "mean_pause": statistics.mean(pauses),
                    "median_pause": statistics.median(pauses),
                    "max_pause": max(pauses),
                    "hesitation_rate": sum(1 for p in pauses if p > pause_threshold)
                    / len(pauses),
                    "sample_size": len(pauses),
                }

        # Identify most hesitant keys
        hesitant_keys = sorted(
            key_hesitation_stats.items(), key=lambda x: x[1]["mean_pause"], reverse=True
        )[:20]

        # Pause distribution analysis
        all_pauses = [
            event.pause_before for event in self.events if event.pause_before > 0
        ]
        pause_distribution = {
            "mean": statistics.mean(all_pauses) if all_pauses else 0,
            "median": statistics.median(all_pauses) if all_pauses else 0,
            "std_dev": statistics.stdev(all_pauses) if len(all_pauses) > 1 else 0,
            "percentiles": {
                "25th": np.percentile(all_pauses, 25) if all_pauses else 0,
                "75th": np.percentile(all_pauses, 75) if all_pauses else 0,
                "90th": np.percentile(all_pauses, 90) if all_pauses else 0,
                "95th": np.percentile(all_pauses, 95) if all_pauses else 0,
            },
        }

        return {
            "key_hesitation_stats": key_hesitation_stats,
            "hesitant_keys": hesitant_keys,
            "pause_distribution": pause_distribution,
            "app_pause_patterns": {
                app: statistics.mean(pauses)
                for app, pauses in app_pauses.items()
                if len(pauses) > 10
            },
            "total_pauses": len(all_pauses),
            "long_pauses": sum(1 for p in all_pauses if p > 2.0),
        }

    def analyze_efficiency_metrics(self) -> Dict[str, Any]:
        """Analyze typing efficiency and performance metrics."""
        logging.info("Analyzing efficiency metrics...")

        if not self.events:
            return {}

        # Time-based analysis
        session_duration = (
            self.events[-1].timestamp - self.events[0].timestamp
        ) / 60  # minutes

        # WPM calculation
        overall_wpm = calculate_wpm(self.events, session_duration * 60)

        # App-specific WPM
        app_events = defaultdict(list)
        for event in self.events:
            app_events[event.app_name].append(event)

        app_wpm = {}
        for app, events in app_events.items():
            if len(events) > 50:  # Minimum for meaningful WPM
                duration = events[-1].timestamp - events[0].timestamp
                if duration > 30:  # At least 30 seconds
                    app_wpm[app] = calculate_wpm(events, duration)

        # Typing burst analysis
        burst_events = [e for e in self.events if e.typing_burst]
        burst_percentage = (len(burst_events) / len(self.events)) * 100

        # Flow state detection
        flow_threshold = self.config.get("analysis.flow_state_threshold", 60)
        flow_periods = self._detect_flow_states(min_keystrokes=flow_threshold)

        # Efficiency ratios
        correction_events = [e for e in self.events if e.is_correction]
        efficiency_ratio = (
            (len(self.events) - len(correction_events)) / len(self.events)
        ) * 100

        # Keystroke consistency (coefficient of variation for inter-keystroke intervals)
        intervals = [e.time_since_last for e in self.events if e.time_since_last > 0]
        consistency_score = 0
        if intervals:
            mean_interval = statistics.mean(intervals)
            std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
            consistency_score = (
                (std_interval / mean_interval) if mean_interval > 0 else 0
            )

        return {
            "overall_wpm": overall_wpm,
            "session_duration_minutes": session_duration,
            "app_specific_wpm": app_wpm,
            "burst_typing_percentage": burst_percentage,
            "flow_state_periods": flow_periods,
            "efficiency_ratio": efficiency_ratio,
            "consistency_score": consistency_score,
            "correction_percentage": (len(correction_events) / len(self.events)) * 100,
            "peak_wpm": max(app_wpm.values()) if app_wpm else overall_wpm,
        }

    def analyze_finger_usage(self) -> Dict[str, Any]:
        """Analyze finger usage patterns and load distribution."""
        logging.info("Analyzing finger usage patterns...")

        finger_counts: Dict[str, int] = defaultdict(int)
        finger_times: Dict[str, float] = defaultdict(float)
        hand_balance = {"left": 0, "right": 0, "thumbs": 0}

        for event in self.events:
            finger = event.finger_assignment or "unknown"
            finger_counts[finger] += 1
            finger_times[finger] += event.dwell_time

            # Hand balance
            if "left" in finger:
                hand_balance["left"] += 1
            elif "right" in finger:
                hand_balance["right"] += 1
            elif finger in ["thumbs", "thumb"]:
                hand_balance["thumbs"] += 1

        total_keystrokes = len(self.events)
        finger_percentages = {
            finger: (count / total_keystrokes) * 100
            for finger, count in finger_counts.items()
        }

        # Same-finger bigram detection (inefficient sequences)
        same_finger_bigrams = []
        for i in range(1, len(self.events)):
            prev_finger = self.events[i - 1].finger_assignment
            curr_finger = self.events[i].finger_assignment
            if prev_finger and curr_finger and prev_finger == curr_finger:
                bigram = (
                    f"{self.events[i - 1].key_char or self.events[i - 1].key_name}"
                    f"{self.events[i].key_char or self.events[i].key_name}"
                )
                same_finger_bigrams.append(bigram)

        same_finger_frequency = Counter(same_finger_bigrams).most_common(20)

        return {
            "finger_usage_counts": dict(finger_counts),
            "finger_usage_percentages": finger_percentages,
            "hand_balance": hand_balance,
            "finger_dwell_times": dict(finger_times),
            "most_used_finger": (
                max(finger_counts.items(), key=lambda x: x[1])[0]
                if finger_counts
                else "unknown"
            ),
            "least_used_finger": (
                min(finger_counts.items(), key=lambda x: x[1])[0]
                if finger_counts
                else "unknown"
            ),
            "same_finger_bigrams": same_finger_frequency,
            "hand_balance_ratio": hand_balance["left"] / max(hand_balance["right"], 1),
        }

    def analyze_cognitive_load(self) -> Dict[str, Any]:
        """Analyze cognitive load indicators from typing patterns."""
        logging.info("Analyzing cognitive load patterns...")

        load_indicators = [
            e.cognitive_load_indicator
            for e in self.events
            if e.cognitive_load_indicator is not None
        ]

        if not load_indicators:
            return {"error": "No cognitive load data available"}

        # App-specific cognitive load
        app_loads = defaultdict(list)
        for event in self.events:
            if event.cognitive_load_indicator is not None:
                app_loads[event.app_name].append(event.cognitive_load_indicator)

        app_cognitive_load = {
            app: statistics.mean(loads)
            for app, loads in app_loads.items()
            if len(loads) > 10
        }

        # Time-based cognitive load patterns
        hourly_loads = defaultdict(list)
        for event in self.events:
            if event.cognitive_load_indicator is not None:
                hour = datetime.fromtimestamp(event.timestamp).hour
                hourly_loads[hour].append(event.cognitive_load_indicator)

        hourly_cognitive_load = {
            hour: statistics.mean(loads) for hour, loads in hourly_loads.items()
        }

        return {
            "overall_cognitive_load": statistics.mean(load_indicators),
            "cognitive_load_std": (
                statistics.stdev(load_indicators) if len(load_indicators) > 1 else 0
            ),
            "high_load_events": sum(1 for load in load_indicators if load > 0.7),
            "app_cognitive_load": app_cognitive_load,
            "hourly_cognitive_load": hourly_cognitive_load,
            "peak_load_hour": (
                max(hourly_cognitive_load.items(), key=lambda x: x[1])[0]
                if hourly_cognitive_load
                else None
            ),
            "lowest_load_hour": (
                min(hourly_cognitive_load.items(), key=lambda x: x[1])[0]
                if hourly_cognitive_load
                else None
            ),
        }

    def _detect_flow_states(self, min_keystrokes: int = 60) -> List[Dict[str, Any]]:
        """Detect periods of sustained, efficient typing (flow states)."""
        flow_periods = []
        current_flow_start = None
        consistent_typing_count = 0

        for i, event in enumerate(self.events):
            # Flow criteria: consistent timing, low correction rate, sustained period
            is_flowing = (
                event.typing_burst
                and not event.is_correction
                and event.pause_before < 0.5
            )

            if is_flowing:
                if current_flow_start is None:
                    current_flow_start = i
                consistent_typing_count += 1
            else:
                if (
                    current_flow_start is not None
                    and consistent_typing_count >= min_keystrokes
                ):
                    # End of flow period
                    flow_start_time = self.events[current_flow_start].timestamp
                    flow_end_time = self.events[i - 1].timestamp
                    duration = flow_end_time - flow_start_time

                    flow_events = self.events[current_flow_start:i]
                    flow_wpm = calculate_wpm(flow_events, duration)

                    flow_periods.append(
                        {
                            "start_time": flow_start_time,
                            "end_time": flow_end_time,
                            "duration_seconds": duration,
                            "keystroke_count": len(flow_events),
                            "wpm": flow_wpm,
                            "app_name": self.events[current_flow_start].app_name,
                        }
                    )

                current_flow_start = None
                consistent_typing_count = 0

        # Handle case where flow continues to end of data
        if current_flow_start is not None and consistent_typing_count >= min_keystrokes:
            flow_start_time = self.events[current_flow_start].timestamp
            flow_end_time = self.events[-1].timestamp
            duration = flow_end_time - flow_start_time

            flow_events = self.events[current_flow_start:]
            flow_wpm = calculate_wpm(flow_events, duration)

            flow_periods.append(
                {
                    "start_time": flow_start_time,
                    "end_time": flow_end_time,
                    "duration_seconds": duration,
                    "keystroke_count": len(flow_events),
                    "wpm": flow_wpm,
                    "app_name": self.events[current_flow_start].app_name,
                }
            )

        return flow_periods

    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Comprehensive analysis of typing errors and correction patterns."""
        logging.info("Analyzing error patterns and corrections...")
        
        # Basic error metrics
        total_corrections = sum(1 for e in self.events if e.is_correction)
        total_keystrokes = len(self.events)
        error_rate = (total_corrections / total_keystrokes * 100) if total_keystrokes > 0 else 0
        
        # Correction sequence analysis
        correction_sequences = []
        current_sequence = []
        
        for event in self.events:
            if event.is_correction:
                current_sequence.append(event)
            else:
                if current_sequence:
                    # End of correction sequence
                    correction_sequences.append({
                        'length': len(current_sequence),
                        'timestamp': current_sequence[0].timestamp,
                        'corrected_chars': [e.corrected_text for e in current_sequence if e.corrected_text],
                        'app_name': current_sequence[0].app_name
                    })
                    current_sequence = []
        
        # Add final sequence if it exists
        if current_sequence:
            correction_sequences.append({
                'length': len(current_sequence),
                'timestamp': current_sequence[0].timestamp,
                'corrected_chars': [e.corrected_text for e in current_sequence if e.corrected_text],
                'app_name': current_sequence[0].app_name
            })
        
        # Analyze correction types
        correction_types = Counter()
        for event in self.events:
            if event.correction_type:
                correction_types[event.correction_type] += 1
        
        # Typo pattern analysis
        typo_patterns = Counter()
        likely_typos = 0
        for event in self.events:
            if event.likely_typo and event.typo_pattern:
                typo_patterns[event.typo_pattern] += 1
                likely_typos += 1
        
        # Error rate by application
        app_errors = defaultdict(lambda: {'corrections': 0, 'total': 0})
        for event in self.events:
            app_errors[event.app_name]['total'] += 1
            if event.is_correction:
                app_errors[event.app_name]['corrections'] += 1
        
        app_error_rates = {}
        for app, data in app_errors.items():
            if data['total'] >= 20:  # Only apps with significant usage
                app_error_rates[app] = (data['corrections'] / data['total'] * 100)
        
        # Time-based error analysis
        hourly_errors = defaultdict(lambda: {'corrections': 0, 'total': 0})
        for event in self.events:
            hour = datetime.fromtimestamp(event.timestamp).hour
            hourly_errors[hour]['total'] += 1
            if event.is_correction:
                hourly_errors[hour]['corrections'] += 1
        
        hourly_error_rates = {}
        for hour, data in hourly_errors.items():
            if data['total'] >= 10:
                hourly_error_rates[hour] = (data['corrections'] / data['total'] * 100)
        
        # Character-specific error analysis
        char_before_correction = []
        for i, event in enumerate(self.events):
            if event.is_correction and i > 0:
                prev_event = self.events[i-1]
                if prev_event.key_char and not prev_event.is_correction:
                    char_before_correction.append(prev_event.key_char)
        
        error_prone_chars = Counter(char_before_correction)
        
        # Correction efficiency (how quickly errors are fixed)
        correction_delays = []
        for seq in correction_sequences:
            if len(seq['corrected_chars']) > 0:
                # Simple efficiency metric based on sequence length
                efficiency = 1.0 / seq['length'] if seq['length'] > 0 else 1.0
                correction_delays.append(efficiency)
        
        avg_correction_efficiency = statistics.mean(correction_delays) if correction_delays else 0
        
        return {
            'total_corrections': total_corrections,
            'overall_error_rate': error_rate,
            'correction_sequences': len(correction_sequences),
            'avg_correction_length': statistics.mean([seq['length'] for seq in correction_sequences]) if correction_sequences else 0,
            'max_correction_length': max([seq['length'] for seq in correction_sequences]) if correction_sequences else 0,
            'correction_types': dict(correction_types),
            'typo_patterns': dict(typo_patterns.most_common(10)),
            'likely_typos_detected': likely_typos,
            'error_prone_chars': dict(error_prone_chars.most_common(10)),
            'app_error_rates': dict(sorted(app_error_rates.items(), key=lambda x: x[1], reverse=True)),
            'hourly_error_rates': dict(hourly_error_rates),
            'correction_efficiency': avg_correction_efficiency,
            'error_frequency': total_corrections / (total_keystrokes / 100) if total_keystrokes > 0 else 0,  # Errors per 100 keystrokes
        }

    def analyze_word_patterns(self) -> Dict[str, Any]:
        """Analyze word and phrase patterns for optimization opportunities."""
        logging.info("Analyzing word and phrase patterns...")
        
        # Reconstruct text from keystrokes
        text_segments = []
        current_word = ""
        
        for event in self.events:
            if event.is_correction:
                # Remove last character on backspace/delete
                if current_word:
                    current_word = current_word[:-1]
            elif event.key_char and event.key_char.isprintable():
                if event.key_char == ' ':
                    if current_word:
                        text_segments.append(current_word.lower())
                        current_word = ""
                else:
                    current_word += event.key_char
        
        # Add final word
        if current_word:
            text_segments.append(current_word.lower())
        
        # Word frequency analysis
        word_counts = Counter(text_segments)
        total_words = len(text_segments)
        
        # Phrase analysis (2-3 word combinations)
        bigrams = []
        trigrams = []
        
        for i in range(len(text_segments) - 1):
            bigrams.append(f"{text_segments[i]} {text_segments[i+1]}")
        
        for i in range(len(text_segments) - 2):
            trigrams.append(f"{text_segments[i]} {text_segments[i+1]} {text_segments[i+2]}")
        
        bigram_counts = Counter(bigrams)
        trigram_counts = Counter(trigrams)
        
        # Calculate typing efficiency for common words
        word_efficiency = {}
        for word, count in word_counts.most_common(20):
            if count >= 3:  # Only analyze words typed multiple times
                word_keystrokes = len(word) * count
                word_efficiency[word] = {
                    'frequency': count,
                    'percentage': (count / total_words) * 100,
                    'total_keystrokes': word_keystrokes,
                    'potential_shortcuts': len(word) > 6  # Long words are shortcut candidates
                }
        
        return {
            'total_words': total_words,
            'unique_words': len(word_counts),
            'most_frequent_words': word_counts.most_common(20),
            'most_frequent_bigrams': bigram_counts.most_common(10),
            'most_frequent_trigrams': trigram_counts.most_common(10),
            'word_efficiency': word_efficiency,
            'vocabulary_size': len(word_counts),
            'repetition_rate': sum(1 for count in word_counts.values() if count > 1) / len(word_counts) if word_counts else 0
        }

    def analyze_key_combinations(self) -> Dict[str, Any]:
        """Analyze key combinations and sequences for optimization."""
        logging.info("Analyzing key combinations and sequences...")
        
        # Character bigrams and trigrams
        char_sequences = []
        for i in range(len(self.events) - 1):
            if (self.events[i].key_char and self.events[i+1].key_char and 
                not self.events[i].is_correction and not self.events[i+1].is_correction):
                bigram = f"{self.events[i].key_char}{self.events[i+1].key_char}"
                char_sequences.append(bigram)
        
        bigram_counts = Counter(char_sequences)
        
        # Same-finger sequences (inefficient)
        same_finger_sequences = []
        for i in range(len(self.events) - 1):
            curr_finger = self.events[i].finger_assignment
            next_finger = self.events[i+1].finger_assignment
            
            if (curr_finger and next_finger and curr_finger == next_finger and 
                self.events[i].key_char and self.events[i+1].key_char):
                sequence = f"{self.events[i].key_char}{self.events[i+1].key_char}"
                same_finger_sequences.append(sequence)
        
        same_finger_counts = Counter(same_finger_sequences)
        
        # Hand alternation analysis
        hand_switches = 0
        total_sequences = 0
        
        for i in range(len(self.events) - 1):
            curr_finger = self.events[i].finger_assignment
            next_finger = self.events[i+1].finger_assignment
            
            if curr_finger and next_finger:
                total_sequences += 1
                curr_hand = 'left' if 'left' in curr_finger else 'right' if 'right' in curr_finger else 'thumb'
                next_hand = 'left' if 'left' in next_finger else 'right' if 'right' in next_finger else 'thumb'
                
                if curr_hand != next_hand:
                    hand_switches += 1
        
        hand_alternation_rate = (hand_switches / total_sequences * 100) if total_sequences > 0 else 0
        
        return {
            'most_common_bigrams': bigram_counts.most_common(20),
            'same_finger_sequences': same_finger_counts.most_common(15),
            'hand_alternation_rate': hand_alternation_rate,
            'total_bigrams': len(char_sequences),
            'inefficient_sequences': len(same_finger_sequences),
            'efficiency_score': max(0, 100 - (len(same_finger_sequences) / len(char_sequences) * 100)) if char_sequences else 0
        }

    def analyze_optimization_opportunities(self) -> Dict[str, Any]:
        """Identify specific optimization opportunities for typing efficiency."""
        logging.info("Analyzing optimization opportunities...")
        
        opportunities = []
        
        # Get word patterns and key combinations
        word_patterns = self.analyze_word_patterns()
        key_combinations = self.analyze_key_combinations()
        
        # 1. Shortcut opportunities for frequent long words
        for word, data in word_patterns['word_efficiency'].items():
            if data['potential_shortcuts'] and data['frequency'] >= 5:
                savings = data['total_keystrokes'] - (data['frequency'] * 3)  # Assume 3-key shortcut
                opportunities.append({
                    'type': 'text_shortcut',
                    'description': f"Create shortcut for '{word}' (typed {data['frequency']} times)",
                    'potential_savings': f"{savings} keystrokes",
                    'priority': 'high' if data['frequency'] > 10 else 'medium'
                })
        
        # 2. Same-finger sequence optimization
        for sequence, count in key_combinations['same_finger_sequences'][:5]:
            if count >= 3:
                opportunities.append({
                    'type': 'finger_optimization',
                    'description': f"'{sequence}' uses same finger {count} times - consider alternative layout",
                    'potential_savings': f"Reduce strain, increase speed",
                    'priority': 'medium'
                })
        
        # 3. Common phrase shortcuts
        for phrase, count in word_patterns['most_frequent_bigrams'][:5]:
            if count >= 3:
                phrase_length = len(phrase.replace(' ', ''))
                savings = count * (phrase_length - 4)  # Assume 4-key shortcut
                if savings > 20:
                    opportunities.append({
                        'type': 'phrase_shortcut',
                        'description': f"Create shortcut for '{phrase}' (used {count} times)",
                        'potential_savings': f"{savings} keystrokes",
                        'priority': 'high' if count > 5 else 'medium'
                    })
        
        # 4. Hand balance improvement
        finger_usage = self.analyze_finger_usage()
        hand_balance = finger_usage['hand_balance']
        total_keystrokes = sum(hand_balance.values())
        
        if total_keystrokes > 0:
            left_percentage = (hand_balance.get('left', 0) / total_keystrokes) * 100
            right_percentage = (hand_balance.get('right', 0) / total_keystrokes) * 100
            
            if abs(left_percentage - right_percentage) > 20:
                dominant_hand = 'left' if left_percentage > right_percentage else 'right'
                opportunities.append({
                    'type': 'hand_balance',
                    'description': f"Hand usage imbalance: {dominant_hand} hand used {max(left_percentage, right_percentage):.1f}% of time",
                    'potential_savings': "Better ergonomics and reduced fatigue",
                    'priority': 'medium'
                })
        
        # 5. Flow state optimization
        efficiency_metrics = self.analyze_efficiency_metrics()
        if efficiency_metrics.get('flow_state_periods', []):
            avg_flow_duration = statistics.mean([p['duration_seconds'] for p in efficiency_metrics['flow_state_periods']])
            if avg_flow_duration < 120:  # Less than 2 minutes
                opportunities.append({
                    'type': 'flow_optimization',
                    'description': f"Short flow states (avg {avg_flow_duration:.1f}s) - minimize interruptions",
                    'potential_savings': "Increase sustained productivity periods",
                    'priority': 'high'
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        opportunities.sort(key=lambda x: priority_order.get(x['priority'], 2))
        
        return {
            'total_opportunities': len(opportunities),
            'high_priority': len([o for o in opportunities if o['priority'] == 'high']),
            'medium_priority': len([o for o in opportunities if o['priority'] == 'medium']),
            'opportunities': opportunities[:10],  # Top 10 opportunities
            'estimated_total_savings': sum([
                int(re.search(r'(\d+)', o['potential_savings']).group(1)) 
                for o in opportunities 
                if 'keystrokes' in o['potential_savings'] and re.search(r'(\d+)', o['potential_savings'])
            ])
        }

    def run_full_analysis(self) -> Dict[str, Any]:
        """Run comprehensive analysis on loaded data."""
        logging.info("Running full typing pattern analysis...")

        if not self.events:
            logging.error("No data loaded for analysis")
            return {}

        self.analysis_results = {
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_events": len(self.events),
                "time_range": {
                    "start": datetime.fromtimestamp(
                        self.events[0].timestamp
                    ).isoformat(),
                    "end": datetime.fromtimestamp(
                        self.events[-1].timestamp
                    ).isoformat(),
                },
            },
            "key_usage": self.analyze_key_usage(),
            "hesitation_patterns": self.analyze_hesitation_patterns(),
            "efficiency_metrics": self.analyze_efficiency_metrics(),
            "finger_usage": self.analyze_finger_usage(),
            "cognitive_load": self.analyze_cognitive_load(),
            "error_patterns": self.analyze_error_patterns(),
            "word_patterns": self.analyze_word_patterns(),
            "key_combinations": self.analyze_key_combinations(),
            "optimization_opportunities": self.analyze_optimization_opportunities(),
        }

        return self.analysis_results

    def generate_reports(self, formats: Optional[List[str]] = None) -> Dict[str, str]:
        """Generate analysis reports in specified formats."""
        if not self.analysis_results:
            logging.error("No analysis results available. Run analysis first.")
            return {}

        formats = formats or self.config.get(
            "reporting.export_formats", ["json", "html"]
        )
        generated_files = {}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for format_type in formats:
            if format_type == "json":
                filename = self.reports_dir / f"typing_analysis_{timestamp}.json"
                with open(filename, "w") as f:
                    json.dump(self.analysis_results, f, indent=2, default=str)
                generated_files["json"] = str(filename)

            elif format_type == "html":
                filename = self.reports_dir / f"typing_analysis_{timestamp}.html"
                self._generate_html_report(filename)
                generated_files["html"] = str(filename)

            elif format_type == "csv":
                filename = self.reports_dir / f"typing_data_{timestamp}.csv"
                self._export_csv_data(filename)
                generated_files["csv"] = str(filename)

        logging.info(f"Generated reports: {list(generated_files.keys())}")
        return generated_files

    def _generate_html_report(self, filename: Path) -> None:
        """Generate comprehensive HTML report with visualizations."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Typing Pattern Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .metric {{ background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .highlight {{ color: #2196F3; font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Typing Pattern Analysis Report</h1>
            <p>Generated: {self.analysis_results['metadata']['analysis_timestamp']}</p>
            
            <div class="metric">
                <h2>Summary Statistics</h2>
                <p>Total Keystrokes: <span class="highlight">{self.analysis_results['key_usage']['total_keystrokes']:,}</span></p>
                <p>Overall WPM: <span class="highlight">{self.analysis_results['efficiency_metrics'].get('overall_wpm', 0):.1f}</span></p>
                <p>Efficiency Ratio: <span class="highlight">{self.analysis_results['efficiency_metrics'].get('efficiency_ratio', 0):.1f}%</span></p>
                <p>Session Duration: <span class="highlight">{self.analysis_results['efficiency_metrics'].get('session_duration_minutes', 0):.1f} minutes</span></p>
            </div>
            
            <div class="metric">
                <h2>Most Frequent Characters</h2>
                <table>
                    <tr><th>Character</th><th>Count</th><th>Percentage</th></tr>
        """

        # Add most frequent characters
        most_frequent = self.analysis_results["key_usage"]["most_frequent_chars"]
        for char, count in most_frequent[:10]:
            char_frequencies = self.analysis_results["key_usage"]["character_frequencies"]
            percentage = char_frequencies.get(char, 0)
            html_content += (
                f"<tr><td>{char}</td><td>{count}</td><td>{percentage:.2f}%</td></tr>"
            )

        html_content += """
                </table>
            </div>
            
            <div class="metric">
                <h2>Finger Usage Distribution</h2>
                <table>
                    <tr><th>Finger</th><th>Usage Count</th><th>Percentage</th></tr>
        """

        # Add finger usage data
        finger_usage = self.analysis_results["finger_usage"]["finger_usage_counts"]
        finger_percentages = self.analysis_results["finger_usage"]["finger_usage_percentages"]

        for finger, count in sorted(
            finger_usage.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = finger_percentages.get(finger, 0)
            html_content += (
                f"<tr><td>{finger.replace('_', ' ').title()}</td>"
                f"<td>{count}</td><td>{percentage:.2f}%</td></tr>"
            )

        html_content += """
                </table>
            </div>
            
            <div class="metric">
                <h2>Word & Phrase Patterns</h2>
                <h3>Most Frequent Words</h3>
                <table>
                    <tr><th>Word</th><th>Count</th><th>Percentage</th></tr>
        """
        
        # Add word frequency data
        for word, count in self.analysis_results['word_patterns']['most_frequent_words'][:10]:
            percentage = (count / self.analysis_results['word_patterns']['total_words']) * 100
            html_content += f"<tr><td>{word}</td><td>{count}</td><td>{percentage:.2f}%</td></tr>"
        
        html_content += """
                </table>
                
                <h3>Most Frequent Phrases</h3>
                <table>
                    <tr><th>Phrase</th><th>Count</th></tr>
        """
        
        # Add phrase frequency data
        for phrase, count in self.analysis_results['word_patterns']['most_frequent_bigrams'][:5]:
            html_content += f"<tr><td>{phrase}</td><td>{count}</td></tr>"
        
        html_content += """
                </table>
            </div>
            
            <div class="metric">
                <h2>Key Combinations & Efficiency</h2>
                <h3>Most Common Character Sequences</h3>
                <table>
                    <tr><th>Sequence</th><th>Count</th></tr>
        """
        
        # Add key combination data
        for sequence, count in self.analysis_results['key_combinations']['most_common_bigrams'][:10]:
            html_content += f"<tr><td>{sequence}</td><td>{count}</td></tr>"
        
        html_content += f"""
                </table>
                <p><strong>Hand Alternation Rate:</strong> <span class="highlight">{self.analysis_results['key_combinations']['hand_alternation_rate']:.1f}%</span></p>
                <p><strong>Typing Efficiency Score:</strong> <span class="highlight">{self.analysis_results['key_combinations']['efficiency_score']:.1f}%</span></p>
            </div>
            
            <div class="metric">
                <h2>⚠️ Error Analysis & Corrections</h2>
                <p><strong>Overall Error Rate:</strong> <span class="highlight">{self.analysis_results['error_patterns']['overall_error_rate']:.2f}%</span></p>
                <p><strong>Total Corrections:</strong> <span class="highlight">{self.analysis_results['error_patterns']['total_corrections']:,}</span></p>
                <p><strong>Correction Sequences:</strong> <span class="highlight">{self.analysis_results['error_patterns']['correction_sequences']}</span></p>
                <p><strong>Typos Detected:</strong> <span class="highlight">{self.analysis_results['error_patterns']['likely_typos_detected']}</span></p>
                <p><strong>Correction Efficiency:</strong> <span class="highlight">{self.analysis_results['error_patterns']['correction_efficiency']:.3f}</span></p>
                
                <h3>Error-Prone Characters</h3>
                <table>
                    <tr><th>Character</th><th>Errors Before</th></tr>
        """
        
        # Add error-prone characters
        for char, count in list(self.analysis_results['error_patterns']['error_prone_chars'].items())[:5]:
            html_content += f"<tr><td>{char}</td><td>{count}</td></tr>"
        
        html_content += """
                </table>
                
                <h3>Common Typo Patterns</h3>
                <table>
                    <tr><th>Typo Pattern</th><th>Occurrences</th></tr>
        """
        
        # Add typo patterns
        for pattern, count in list(self.analysis_results['error_patterns']['typo_patterns'].items())[:5]:
            html_content += f"<tr><td>{pattern}</td><td>{count}</td></tr>"
        
        html_content += """
                </table>
                
                <h3>App-Specific Error Rates</h3>
                <table>
                    <tr><th>Application</th><th>Error Rate</th></tr>
        """
        
        # Add app error rates
        for app, rate in list(self.analysis_results['error_patterns']['app_error_rates'].items())[:5]:
            html_content += f"<tr><td>{app}</td><td>{rate:.2f}%</td></tr>"
        
        html_content += """
                </table>
            </div>
            
            <div class="metric">
                <h2>🚀 Optimization Opportunities</h2>
                <p><strong>Total Opportunities Found:</strong> <span class="highlight">{self.analysis_results['optimization_opportunities']['total_opportunities']}</span></p>
                <p><strong>High Priority:</strong> <span class="highlight">{self.analysis_results['optimization_opportunities']['high_priority']}</span> | 
                   <strong>Medium Priority:</strong> <span class="highlight">{self.analysis_results['optimization_opportunities']['medium_priority']}</span></p>
                <p><strong>Estimated Total Savings:</strong> <span class="highlight">{self.analysis_results['optimization_opportunities']['estimated_total_savings']} keystrokes</span></p>
                
                <h3>Top Recommendations</h3>
                <table>
                    <tr><th>Priority</th><th>Type</th><th>Description</th><th>Potential Savings</th></tr>
        """
        
        # Add optimization opportunities
        for opp in self.analysis_results['optimization_opportunities']['opportunities'][:8]:
            priority_color = "#e74c3c" if opp['priority'] == 'high' else "#f39c12" if opp['priority'] == 'medium' else "#27ae60"
            html_content += f"""
                <tr>
                    <td style="color: {priority_color}; font-weight: bold;">{opp['priority'].upper()}</td>
                    <td>{opp['type'].replace('_', ' ').title()}</td>
                    <td>{opp['description']}</td>
                    <td>{opp['potential_savings']}</td>
                </tr>
            """
        
        html_content += """
                </table>
            </div>
        </body>
        </html>
        """

        with open(filename, "w") as f:
            f.write(html_content)

    def _export_csv_data(self, filename: Path) -> None:
        """Export keystroke data to CSV format."""
        data = []
        for event in self.events:
            data.append(
                {
                    "timestamp": datetime.fromtimestamp(event.timestamp),
                    "key_char": event.key_char,
                    "key_name": event.key_name,
                    "dwell_time": event.dwell_time,
                    "time_since_last": event.time_since_last,
                    "app_name": event.app_name,
                    "window_title": event.window_title,
                    "is_correction": event.is_correction,
                    "pause_before": event.pause_before,
                    "typing_burst": event.typing_burst,
                    "finger_assignment": event.finger_assignment,
                    "cognitive_load_indicator": event.cognitive_load_indicator,
                    "correction_type": event.correction_type,
                    "corrected_text": event.corrected_text,
                    "likely_typo": event.likely_typo,
                    "typo_pattern": event.typo_pattern,
                }
            )

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)


def main():
    """Main entry point for the analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Typing Pattern Analysis")
    parser.add_argument(
        "--config", default="config.yaml", help="Configuration file path"
    )
    parser.add_argument("--input", help="Input data directory")
    parser.add_argument(
        "--report-type",
        choices=["all", "summary", "detailed"],
        default="all",
        help="Type of report to generate",
    )
    parser.add_argument(
        "--export-csv", action="store_true", help="Export raw data to CSV"
    )
    parser.add_argument(
        "--visualizations", action="store_true", help="Generate visualizations"
    )
    parser.add_argument("--output", help="Output directory for reports")

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = TypingPatternAnalyzer(args.config)

    # Load data
    analyzer.load_data()

    if not analyzer.events:
        print("No keystroke data found. Please run the keylogger first.")
        return

    # Run analysis
    results = analyzer.run_full_analysis()

    # Generate reports
    report_formats = ["json", "html"]
    if args.export_csv:
        report_formats.append("csv")

    generated_files = analyzer.generate_reports(report_formats)

    # Print summary to console
    print("\n=== Typing Pattern Analysis Summary ===")
    print(f"Total Keystrokes: {results['key_usage']['total_keystrokes']:,}")
    print(f"Overall WPM: {results['efficiency_metrics'].get('overall_wpm', 0):.1f}")
    print(
        f"Efficiency Ratio: {results['efficiency_metrics'].get('efficiency_ratio', 0):.1f}%"
    )
    print(
        f"Session Duration: "
        f"{results['efficiency_metrics'].get('session_duration_minutes', 0):.1f} minutes"
    )
    
    # Add error analysis insights
    if 'error_patterns' in results:
        print(f"\n=== Error Analysis ====")
        print(f"Overall Error Rate: {results['error_patterns']['overall_error_rate']:.2f}%")
        print(f"Total Corrections: {results['error_patterns']['total_corrections']:,}")
        print(f"Correction Efficiency: {results['error_patterns']['correction_efficiency']:.3f}")
        print(f"Typos Detected: {results['error_patterns']['likely_typos_detected']}")
        
        # Show most error-prone character
        if results['error_patterns']['error_prone_chars']:
            top_error_char = list(results['error_patterns']['error_prone_chars'].items())[0]
            print(f"Most Error-Prone Character: '{top_error_char[0]}' ({top_error_char[1]} corrections)")
    
    # Add new pattern insights
    if 'word_patterns' in results:
        print(f"\n=== Word & Pattern Analysis ===")
        print(f"Total Words: {results['word_patterns']['total_words']:,}")
        print(f"Unique Words: {results['word_patterns']['unique_words']:,}")
        print(f"Vocabulary Repetition: {results['word_patterns']['repetition_rate']:.1f}%")
        
        if results['word_patterns']['most_frequent_words']:
            top_word, count = results['word_patterns']['most_frequent_words'][0]
            print(f"Most Frequent Word: '{top_word}' ({count} times)")
    
    if 'key_combinations' in results:
        print(f"\n=== Typing Efficiency ===")
        print(f"Hand Alternation Rate: {results['key_combinations']['hand_alternation_rate']:.1f}%")
        print(f"Typing Efficiency Score: {results['key_combinations']['efficiency_score']:.1f}%")
    
    # Show optimization opportunities
    if 'optimization_opportunities' in results:
        opportunities = results['optimization_opportunities']
        print(f"\n=== 🚀 Optimization Opportunities ===")
        print(f"Total Opportunities: {opportunities['total_opportunities']}")
        print(f"High Priority: {opportunities['high_priority']} | Medium Priority: {opportunities['medium_priority']}")
        print(f"Estimated Savings: {opportunities['estimated_total_savings']} keystrokes")
        
        if opportunities['opportunities']:
            print(f"\nTop Recommendations:")
            for i, opp in enumerate(opportunities['opportunities'][:3], 1):
                priority_emoji = "🔴" if opp['priority'] == 'high' else "🟡" if opp['priority'] == 'medium' else "🟢"
                print(f"  {i}. {priority_emoji} {opp['description']}")
                print(f"     Savings: {opp['potential_savings']}")
                print()

    print("\nReports generated:")
    for format_type, filepath in generated_files.items():
        print(f"  {format_type.upper()}: {filepath}")


if __name__ == "__main__":
    main()
