# ABOUTME: Quick 30-second live keylogger test
from src.keylogger import TypingAnalyzerKeylogger
from src.analyzer import TypingPatternAnalyzer
import time

def quick_live_test():
    """Run a 30-second live keylogger test."""
    
    print("🎯 QUICK LIVE TEST - 30 seconds")
    print("=" * 40)
    print("This will capture your actual keystrokes for 30 seconds.")
    print("Type normally - maybe write a few sentences about anything.")
    print("Press Ctrl+C to stop early if needed.")
    print()
    
    response = input("Ready to start 30-second test? (y/N): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return
    
    print("\n🟢 Starting in 3 seconds...")
    time.sleep(1)
    print("2...")
    time.sleep(1) 
    print("1...")
    time.sleep(1)
    print("GO! Type naturally for 30 seconds...")
    
    # Create keylogger with 30-second timeout
    keylogger = TypingAnalyzerKeylogger('config.yaml')
    
    try:
        import threading
        
        # Stop after 30 seconds
        timer = threading.Timer(30.0, keylogger.stop_monitoring)
        timer.start()
        
        keylogger.start_monitoring()
        
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
        keylogger.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        return
    
    # Quick analysis of the captured data
    print("\n🔍 Analyzing your typing patterns...")
    
    analyzer = TypingPatternAnalyzer('config.yaml')
    analyzer.load_data()
    
    if not analyzer.events:
        print("No keystrokes captured. Make sure accessibility permissions are granted.")
        return
    
    results = analyzer.run_full_analysis()
    
    print(f"\n✨ YOUR RESULTS:")
    print(f"⌨️  Keystrokes: {len(analyzer.events)}")
    print(f"⚡ WPM: {results['efficiency_metrics']['overall_wpm']:.1f}")
    print(f"🎯 Efficiency: {results['efficiency_metrics']['efficiency_ratio']:.1f}%")
    print(f"🧠 Avg Cognitive Load: {results['cognitive_load']['overall_cognitive_load']:.2f}")
    
    # Generate report
    generated_files = analyzer.generate_reports(['html'])
    print(f"\n📄 Detailed report: {generated_files.get('html', 'Not generated')}")

if __name__ == "__main__":
    quick_live_test()