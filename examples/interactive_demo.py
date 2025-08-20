#!/usr/bin/env python3
"""
🎯 Interactive Transformation Demo - Amber-style Code Transformation

This demo shows the interactive transformation capabilities,
similar to the amber search & replace tool.
"""

import tempfile
from pathlib import Path

# Sample code with print statements to transform
SAMPLE_CODE = """
import os
import sys

def process_data(data):
    print("Starting data processing")
    print(f"Processing {len(data)} items")
    
    results = []
    for i, item in enumerate(data):
        print(f"Processing item {i}: {item}")
        if item > 0:
            results.append(item * 2)
        else:
            print(f"Skipping negative item: {item}")
    
    print(f"Processed {len(results)} items successfully")
    return results

def save_results(results, filename):
    print(f"Saving {len(results)} results to {filename}")
    try:
        with open(filename, 'w') as f:
            for result in results:
                print(result, file=f)
        print("Results saved successfully")
    except Exception as e:
        print(f"Error saving results: {e}")

def main():
    print("Demo application starting")
    
    data = [1, -2, 3, 4, -5, 6, 7, 8]
    print(f"Input data: {data}")
    
    results = process_data(data)
    save_results(results, "output.txt")
    
    print("Demo completed")

if __name__ == "__main__":
    main()
"""


def create_demo_file() -> Path:
    """Create a temporary demo file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(SAMPLE_CODE)
        return Path(f.name)


def main():
    """Run the interactive demo."""
    demo_file = create_demo_file()

    print("🎯 Interactive Transformation Demo")
    print("=" * 50)
    print(f"Demo file created: {demo_file}")
    print()
    print("This file contains multiple print() statements that can be")
    print("transformed to structured logging.")
    print()
    print("To run the interactive transformation:")
    print(f"  nicestlog ast interactive {demo_file}")
    print()
    print("Or use the transform command with --interactive:")
    print(f"  nicestlog ast transform {demo_file} --interactive --apply")
    print()
    print("You'll see output like:")
    print()
    print('./demo.py:5                    print("Starting data processing")')
    print(
        '        ->                     log.info("print-message", _replace_msg="Starting data processing")'
    )
    print("Replace keyword? [Y]es/[n]o/[a]ll/[p]review/[s]kip file/[q]uit:")
    print()
    print("Options:")
    print("  Y - Accept this transformation")
    print("  n - Reject this transformation")
    print("  a - Accept all remaining transformations")
    print("  p - Show detailed preview")
    print("  s - Skip remaining transformations in this file")
    print("  q - Quit the session")
    print()
    print(f"Demo file: {demo_file}")
    print("Remember to delete the demo file when done!")


if __name__ == "__main__":
    main()
