#!/usr/bin/env python3
"""
Test script to measure startup timing.
Launches the application, waits for it to initialize, then closes it.
"""

import sys
import os
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment to avoid actual connections
os.environ['TESTING_MODE'] = '1'

def main():
    print("=" * 80)
    print("STARTUP TIMING TEST")
    print("=" * 80)
    print("\nLaunching application with timing instrumentation...")
    print("The application will start and automatically generate timing reports.\n")
    
    # Import and run main
    from main import main as app_main
    
    try:
        # This will run until the window is closed or the app exits
        app_main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"\nError during startup: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Startup timing test complete. Check logs/startup_timing.json for detailed results.")
    print("=" * 80)

if __name__ == "__main__":
    main()
