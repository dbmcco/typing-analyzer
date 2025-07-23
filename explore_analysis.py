# ABOUTME: Interactive exploration of analysis features
from src.analyzer import TypingPatternAnalyzer
from src.utils import KeystrokeEvent
import time
import json

def explore_different_scenarios():
    """Explore how different typing scenarios affect the analysis."""
    
    scenarios = {
        "focused_programmer": {
            "desc": "Focused programmer writing clean code",
            "apps": [("PyCharm", "main.py"), ("Terminal", "bash")],
            "wpm_range": (45, 65),
            "cognitive_load": (0.4, 0.7),
            "correction_rate": 0.03,
            "pause_factor": 1.2
        },
        "casual_chatter": {
            "desc": "Casual messaging and social media",
            "apps": [("Slack", "General"), ("Chrome", "Twitter")],
            "wpm_range": (35, 55),
            "cognitive_load": (0.1, 0.3),
            "correction_rate": 0.08,
            "pause_factor": 0.8
        },
        "stressed_writer": {
            "desc": "Writer on deadline, high pressure",
            "apps": [("TextEdit", "Article.docx"), ("Chrome", "Research")],
            "wpm_range": (25, 45),
            "cognitive_load": (0.6, 0.9),
            "correction_rate": 0.12,
            "pause_factor": 2.0
        },
        "flow_state_coder": {
            "desc": "Developer in deep flow state",
            "apps": [("PyCharm", "algorithm.py")],
            "wpm_range": (65, 85),
            "cognitive_load": (0.2, 0.4),
            "correction_rate": 0.01,
            "pause_factor": 0.6
        }
    }
    
    print("🎭 TYPING SCENARIO EXPLORER")
    print("=" * 50)
    print("Let's see how different typing situations affect the analysis!")
    print()
    
    for name, scenario in scenarios.items():
        print(f"🎯 Analyzing: {scenario['desc']}")
        
        # Generate scenario-specific data
        events = create_scenario_data(scenario, 400)
        
        # Run analysis
        analyzer = TypingPatternAnalyzer('config.yaml')
        analyzer.events = events
        results = analyzer.run_full_analysis()
        
        # Show key metrics
        print(f"   ⚡ WPM: {results['efficiency_metrics']['overall_wpm']:.1f}")
        print(f"   🎯 Efficiency: {results['efficiency_metrics']['efficiency_ratio']:.1f}%")
        print(f"   🧠 Cognitive Load: {results['cognitive_load']['overall_cognitive_load']:.2f}")
        print(f"   ⏸️  Long Pauses: {results['hesitation_patterns']['long_pauses']}")
        print(f"   🔄 Corrections: {results['key_usage']['total_corrections']}")
        print()
    
    print("💡 Notice how cognitive load, efficiency, and pause patterns")
    print("   change dramatically based on the typing context!")

def create_scenario_data(scenario, num_keystrokes):
    """Create realistic data for a specific typing scenario."""
    import random
    
    events = []
    base_time = time.time()
    current_time = base_time
    
    # Text to type (realistic programming/writing content)
    sample_text = "def analyze_typing_patterns(data): return statistical_analysis(data)"
    
    for i in range(num_keystrokes):
        # Pick app context
        app_name, window_title = random.choice(scenario["apps"])
        
        # Get character
        char = sample_text[i % len(sample_text)]
        
        # Scenario-specific timing
        base_interval = 60.0 / random.uniform(*scenario["wpm_range"]) / 5  # 5 chars per word
        time_delta = base_interval * scenario["pause_factor"] * random.uniform(0.5, 1.5)
        
        # Add corrections
        is_correction = random.random() < scenario["correction_rate"]
        if is_correction:
            char = ""
            key_name = "backspace"
            time_delta *= 1.5
        else:
            key_name = char
        
        current_time += time_delta
        
        # Create event
        event = KeystrokeEvent(
            timestamp=current_time,
            key_code=hash(char or key_name),
            key_char=char,
            key_name=key_name,
            dwell_time=random.uniform(0.06, 0.12),
            time_since_last=time_delta,
            app_name=app_name,
            window_title=window_title,
            session_id=f"scenario-{scenario['desc'][:10]}",
            is_correction=is_correction,
            pause_before=time_delta if time_delta > 0.1 else 0.0,
            typing_burst=time_delta < 0.15,
            finger_assignment='right_index',  # Simplified
            cognitive_load_indicator=random.uniform(*scenario["cognitive_load"])
        )
        
        events.append(event)
    
    return events

def interactive_analysis_menu():
    """Interactive menu for exploring analysis features."""
    
    while True:
        print("\n🔍 TYPING ANALYZER EXPLORER")
        print("=" * 30)
        print("1. 📊 Run demo with realistic data")
        print("2. 🎭 Compare different typing scenarios") 
        print("3. ⚡ Quick 30-second live test")
        print("4. 📄 View latest analysis report")
        print("5. 🧪 Custom scenario builder")
        print("6. ❌ Exit")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            print("\n" + "="*50)
            exec(open("test_demo.py").read())
            
        elif choice == "2":
            print("\n" + "="*50)
            explore_different_scenarios()
            
        elif choice == "3":
            print("\n" + "="*50)
            exec(open("quick_test.py").read())
            
        elif choice == "4":
            print("\n📄 Opening latest report...")
            import os
            reports_dir = "reports"
            if os.path.exists(reports_dir):
                html_files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
                if html_files:
                    latest = max(html_files)
                    print(f"Latest report: {reports_dir}/{latest}")
                    print("Open this file in your browser to view the detailed analysis!")
                else:
                    print("No HTML reports found. Run an analysis first!")
            
        elif choice == "5":
            print("\n🧪 Custom Scenario Builder")
            print("This would let you create custom typing scenarios...")
            print("(Feature placeholder - could be expanded!)")
            
        elif choice == "6":
            print("\n👋 Thanks for testing the typing analyzer!")
            break
            
        else:
            print("❌ Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    interactive_analysis_menu()