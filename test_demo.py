# ABOUTME: Safe demonstration script for typing analyzer testing
from src.analyzer import TypingPatternAnalyzer
from src.utils import KeystrokeEvent
import time
import random

def create_realistic_sample_data(num_keystrokes=500):
    """Create realistic sample typing data for testing."""
    
    # Common English text patterns
    common_words = [
        "the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog",
        "hello", "world", "python", "typing", "analysis", "pattern",
        "keyboard", "efficiency", "speed", "accuracy", "performance"
    ]
    
    # Different typing contexts
    contexts = [
        ("TextEdit", "Document.txt"),
        ("Terminal", "Terminal"),
        ("PyCharm", "main.py"),
        ("Slack", "General"),
        ("Chrome", "GitHub - typing-analyzer")
    ]
    
    events = []
    base_time = time.time()
    session_id = "demo-session"
    
    current_time = base_time
    word_idx = 0
    context_idx = 0
    
    for i in range(num_keystrokes):
        # Switch context occasionally
        if i % 100 == 0:
            context_idx = (context_idx + 1) % len(contexts)
        
        app_name, window_title = contexts[context_idx]
        
        # Get next character from word sequence
        current_word = common_words[word_idx % len(common_words)]
        char_in_word = i % len(current_word)
        
        if char_in_word == 0 and i > 0:
            # Add space between words
            key_char = " "
            key_name = "space"
        else:
            key_char = current_word[char_in_word]
            key_name = key_char
            
        if char_in_word == len(current_word) - 1:
            word_idx += 1
        
        # Realistic timing variations
        if key_char == " ":
            # Longer pauses at word boundaries
            time_delta = random.uniform(0.2, 0.4)
        elif char_in_word == 0:
            # Slight hesitation at word start
            time_delta = random.uniform(0.15, 0.25)
        else:
            # Normal typing rhythm
            time_delta = random.uniform(0.08, 0.18)
        
        current_time += time_delta
        
        # Occasional corrections (backspace)
        is_correction = random.random() < 0.05  # 5% correction rate
        if is_correction:
            key_char = ""
            key_name = "backspace"
            time_delta = random.uniform(0.1, 0.3)
        
        # Calculate metrics
        pause_before = time_delta if time_delta > 0.1 else 0.0
        typing_burst = time_delta < 0.15
        
        # Cognitive load varies by context
        cognitive_load = {
            "TextEdit": random.uniform(0.2, 0.4),
            "Terminal": random.uniform(0.4, 0.7),
            "PyCharm": random.uniform(0.3, 0.6),
            "Slack": random.uniform(0.1, 0.3),
            "Chrome": random.uniform(0.2, 0.5)
        }[app_name]
        
        # Create event
        event = KeystrokeEvent(
            timestamp=current_time,
            key_code=hash(key_char or key_name),
            key_char=key_char,
            key_name=key_name,
            dwell_time=random.uniform(0.06, 0.12),
            time_since_last=time_delta,
            app_name=app_name,
            window_title=window_title,
            session_id=session_id,
            is_correction=is_correction,
            pause_before=pause_before,
            typing_burst=typing_burst,
            finger_assignment=get_demo_finger(key_char or key_name),
            cognitive_load_indicator=cognitive_load
        )
        
        events.append(event)
    
    return events

def get_demo_finger(key):
    """Simple finger mapping for demo."""
    finger_map = {
        'a': 'left_pinky', 's': 'left_ring', 'd': 'left_middle', 'f': 'left_index',
        'j': 'right_index', 'k': 'right_middle', 'l': 'right_ring', ';': 'right_pinky',
        ' ': 'thumbs', 'backspace': 'right_pinky'
    }
    return finger_map.get(key.lower(), 'right_index')

def run_demo_analysis():
    """Run a complete demonstration of the typing analyzer."""
    
    print("🔍 Creating realistic sample typing data...")
    sample_events = create_realistic_sample_data(500)
    print(f"✅ Generated {len(sample_events)} sample keystrokes")
    
    print("\n📊 Initializing analyzer...")
    analyzer = TypingPatternAnalyzer('config.yaml')
    analyzer.events = sample_events
    
    print("🧮 Running comprehensive analysis...")
    results = analyzer.run_full_analysis()
    
    # Display key results
    print("\n" + "="*50)
    print("📈 TYPING ANALYSIS RESULTS")
    print("="*50)
    
    print(f"📍 Total Keystrokes: {results['key_usage']['total_keystrokes']:,}")
    print(f"⚡ Overall WPM: {results['efficiency_metrics']['overall_wpm']:.1f}")
    print(f"🎯 Efficiency Ratio: {results['efficiency_metrics']['efficiency_ratio']:.1f}%")
    print(f"⏱️  Session Duration: {results['efficiency_metrics']['session_duration_minutes']:.1f} minutes")
    
    print(f"\n🖐️ FINGER USAGE:")
    finger_usage = results['finger_usage']['finger_usage_percentages']
    for finger, percentage in sorted(finger_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {finger.replace('_', ' ').title()}: {percentage:.1f}%")
    
    print(f"\n🧠 COGNITIVE LOAD:")
    print(f"  Overall: {results['cognitive_load']['overall_cognitive_load']:.2f}")
    print(f"  High load events: {results['cognitive_load']['high_load_events']}")
    
    print(f"\n⏸️  HESITATION PATTERNS:")
    print(f"  Total pauses: {results['hesitation_patterns']['total_pauses']}")
    print(f"  Long pauses (>2s): {results['hesitation_patterns']['long_pauses']}")
    
    print(f"\n🏃 FLOW STATES:")
    flow_periods = results['efficiency_metrics']['flow_state_periods']
    print(f"  Flow periods detected: {len(flow_periods)}")
    if flow_periods:
        avg_flow_wpm = sum(p['wpm'] for p in flow_periods) / len(flow_periods)
        print(f"  Average flow WPM: {avg_flow_wpm:.1f}")
    
    print(f"\n📱 APP-SPECIFIC PERFORMANCE:")
    app_wpm = results['efficiency_metrics']['app_specific_wpm']
    for app, wpm in sorted(app_wpm.items(), key=lambda x: x[1], reverse=True):
        print(f"  {app}: {wpm:.1f} WPM")
    
    # Generate reports
    print(f"\n📄 Generating reports...")
    generated_files = analyzer.generate_reports(['json', 'html'])
    
    print(f"\n📋 Reports generated:")
    for format_type, filepath in generated_files.items():
        print(f"  📄 {format_type.upper()}: {filepath}")
    
    print(f"\n✨ Demo completed successfully!")
    print(f"💡 Check the reports/ directory for detailed analysis files")
    
    return results

if __name__ == "__main__":
    run_demo_analysis()